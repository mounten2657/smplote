import threading
import mysql.connector
from functools import wraps
from gevent.lock import Semaphore
from typing import Union, List, Dict, Optional, Any
from dbutils.persistent_db import PersistentDB
from tool.core import Logger, Error, Config, Attr, Time, Str

_mysql_pool = None
_pool_lock = Semaphore()


class MysqlBaseModel:
    """
    Mysql db handler (gevent-compatible version)
    ### Usage examples
      **> Query classes**
         # Initialize the database connection
          db = TestMysqlModel()  # 子类中指定表名
         # Get a single record
          msg_one = db.table('Msg') \
             .select(['id', 'msg']) \
             .where({
                 "wxid": "wx_x123",
                 "msg": {"opt": "like", "val": "%你好%"},
                 "create_time": {"opt": ">", "val": "2025-02-01 00:00:00"}
             }) \
             .first()
          print(msg_one)  # Output: {"id":101,"msg":"你好世界"}

         # Get a paginated list
          msg_list = db.table('Msg') \
              .select(['id', 'msg']) \
              .where({
                  "wxid": "wx_x123",
                  "msg": {"opt": "like", "val": "%你好%"},
                  "create_time": {"opt": ">", "val": "2025-02-01 00:00:00"}
              }) \
              .limit(0, 10) \
              .get()
          print(msg_list)  # Output: [{"id":101,"msg":"你好世界"}, ...]

      **> Operation classes**
         # Execute a custom query SQL
          data = db.query_sql("SELECT id, msg FROM Msg WHERE wxid = 'wx_123' LIMIT 5")

         # Execute a non-query operation (update, delete, index, create table, etc.)
          success = db.exec_sql("UPDATE Msg SET status = 1 WHERE id = 101")
          if success:
              print("Update successful")

      **> Update classes**
         # Update the record with id=100
          affected = db.table('Msg').update(
              {"id": 100},
              {"remark": "u_test1", "user": "joy1"}
          )
          print(f"Updated {affected} records")

         # Batch update two records
          affected = db.table('Msg').update(
              [{"id": 100}, {"id": 102}],
              [
                  {"remark": "u_test1", "user": "joy1"},
                  {"remark": "u_test22", "user": "joy44"}
              ]
          )
          print(f"Batch updated {affected} records")

         # Delete records where wxid is wx_123 and status is 0
          deleted = db.table('Msg').delete({
              "wxid": "wx_123",
              "status": 0
          })
          print(f"Deleted {deleted} records")

         # Delete using operators
          deleted = db.table('Msg').delete({
              "create_time": {"opt": "<", "val": "2025-01-01"}
          })
          print(f"Deleted {deleted} old records")
    """

    _query_lock = threading.Lock()
    _db_config = Config.mysql_db_config()
    _table = None   # 表名，子类继承时指定
    _pool = None

    def __init__(self):
        self.logger = Logger()
        self.prefix = self._db_config['prefix']
        self._table = self.prefix + self._table if self._table else None
        self._state = QueryState(self._table)

    @classmethod
    def get_pool(cls):
        """获取协程安全的数据库连接池"""
        global _mysql_pool
        Time.sleep(Str.randint(1, 30) / 10)
        # 双重检查锁定初始化连接池
        if _mysql_pool is None:
            with _pool_lock:
                if _mysql_pool is None:
                    logger = Logger()
                    logger.warning("----Initializing gevent-compatible MySQL pool----", 'DB_CONN', 'mysql')
                    _mysql_pool = PersistentDB(
                        creator=lambda: mysql.connector.connect(
                            host=cls._db_config['host'],
                            port=cls._db_config['port'],
                            user=cls._db_config['user'],
                            password=cls._db_config['password'],
                            database=cls._db_config['database'],
                            use_pure=True
                        ),
                        maxusage=1000,
                        setsession=['SET autocommit=0'],
                        ping=1
                    )
        return _mysql_pool

    def _get_connection(self):
        """获取数据库连接（每个greenlet独立连接）"""
        try:
            conn = self.get_pool().connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return conn
        except mysql.connector.Error as e:
            self.logger.error(f"Connection ping failed: {e}", 'DB_CONN', 'mysql')
            raise

    def _release_connection(self, conn):
        """安全释放连接回连接池"""
        try:
            conn.close()  # PersistentDB 会处理实际回收
        except Exception as e:
            self.logger.warning(f"Error releasing connection: {str(e)}", 'DB_CONN', 'mysql')

    @staticmethod
    def with_connection(func):
        """连接管理装饰器"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            Time.sleep(0.01)
            conn = self._get_connection()
            try:
                return func(self, conn, *args, **kwargs)
            finally:
                self._release_connection(conn)
                self._state.reset()  # 连接释放后重置状态
        return wrapper

    def table(self, table_name: str) -> 'MysqlBaseModel':
        """设置表名"""
        self._table = table_name
        self._state._table = self._table
        return self

    def table_name(self):
        """获取表名"""
        return self._table

    def select(self, columns: List[str]) -> 'MysqlBaseModel':
        """设置查询字段"""
        self._state._select = columns
        return self

    def where(self, conditions: Dict) -> 'MysqlBaseModel':
        """添加WHERE条件"""
        for field, condition in conditions.items():
            if isinstance(condition, dict):
                operator = condition['opt'].upper()
                value = condition['val']
                self._state._wheres.append((field, operator, value))
            else:
                self._state._wheres.append((field, '=', condition))
        return self

    def where_in(self, key: str, values: List[Any]) -> 'MysqlBaseModel':
        """IN条件查询"""
        if values:
            self._state._where_ins.append((key, values))
        return self

    def where_sql(self, sql: str) -> 'MysqlBaseModel':
        """自定义SQL条件"""
        if sql:
            self._state._where_sqls.append(sql)
        return self

    def order(self, column: str, des: str) -> 'MysqlBaseModel':
        """设置排序"""
        self._state._order_str = self._state._order_str if self._state._order_str else ''
        if not self._state._order_str:
            self._state._order_str = f" ORDER BY {column} {des.upper()} "
        else:
            self._state._order_str += f", {column} {des.upper()} "
        return self

    def limit(self, offset: int, count: int) -> 'MysqlBaseModel':
        """设置分页"""
        self._state._limit_offset = offset
        self._state._limit_count = count
        return self

    def _build_query(self) -> tuple:
        """构建查询SQL"""
        with self._query_lock:
            if not self._table:
                raise ValueError("No table specified")

            # SELECT部分
            select_clause = ', '.join(self._state._select)

            # WHERE部分
            where_parts = []
            params = []

            # 处理普通WHERE条件
            for field, operator, value in self._state._wheres:
                if operator == 'IN':
                    placeholders = ', '.join(['%s'] * len(value))
                    where_parts.append(f"{field} IN ({placeholders})")
                    params.extend(value)
                elif operator == 'BETWEEN':
                    where_parts.append(f"{field} BETWEEN %s AND %s")
                    params.extend(value)
                else:
                    where_parts.append(f"{field} {operator} %s")
                    params.append(value)

            # 处理WHERE IN条件
            for field, values in self._state._where_ins:
                placeholders = ', '.join(['%s'] * len(values))
                where_parts.append(f"{field} IN ({placeholders})")
                params.extend(values)

            if not where_parts and not self._state._where_sqls:
                raise ValueError("No where condition specified")

            where_clause = ' AND '.join(where_parts) if where_parts else '1=1'

            # 处理自定义SQL条件
            for sql in self._state._where_sqls:
                where_clause += f" {sql} "

            # LIMIT部分
            limit_clause = ''
            if self._state._limit_count is not None:
                if self._state._limit_offset is not None:
                    limit_clause = f"LIMIT {self._state._limit_offset}, {self._state._limit_count}"
                else:
                    limit_clause = f"LIMIT {self._state._limit_count}"

            order_str = self._state._order_str if self._state._order_str else ''

            sql = f"SELECT {select_clause} FROM {self._table} WHERE {where_clause} {order_str} {limit_clause}"
            self.logger.debug({"sql": sql.strip(), "params": params}, 'DB_SQL_SELECT', 'mysql')
            return sql.strip(), params

    @with_connection
    def get(self, conn) -> List[Dict]:
        """执行查询并返回所有结果"""
        sql, params = self._build_query()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            return Attr.convert_to_json_dict(cursor.fetchall())
        finally:
            cursor.close()

    @with_connection
    def first(self, conn) -> Optional[Dict]:
        """获取第一条记录"""
        self.limit(0, 1)
        sql, params = self._build_query()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            results = Attr.convert_to_json_dict(cursor.fetchall())
            return results[0] if results else {}
        finally:
            cursor.close()

    @with_connection
    def query_sql(self, conn, sql: str) -> List[Dict]:
        """执行原生查询SQL"""
        cursor = conn.cursor(dictionary=True)
        try:
            self.logger.debug({"sql": sql.strip(), "params": {}}, 'DB_SQL_QUERY', 'mysql')
            cursor.execute(sql)
            if sql.lstrip().upper().startswith('SELECT'):
                return cursor.fetchall()
            return []
        except Exception as e:
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_QUERY_SQL', 'mysql')
            return []
        finally:
            cursor.close()

    @with_connection
    def exec_sql(self, conn, sql: str) -> bool:
        """执行非查询SQL"""
        cursor = conn.cursor()
        try:
            self.logger.info({"sql": sql.strip(), "params": {}}, 'DB_SQL_EXEC', 'mysql')
            cursor.execute(sql)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_EXEC_SQL', 'mysql')
            return False
        finally:
            cursor.close()

    @with_connection
    def update(self, conn, conditions: Union[Dict, List[Dict]], update_data: Union[Dict, List[Dict]]) -> int:
        """
        更新记录（支持单条和批量更新）
        :param conditions: 条件字典或字典列表
        :param update_data: 更新数据字典或字典列表
        :return: 受影响的行数
        """
        if not self._table:
            raise ValueError("No table specified")

        cursor = conn.cursor()
        try:
            update_data_converted = Attr.convert_to_json_string(update_data)
            affected_rows = 0

            # 批量更新模式
            if isinstance(conditions, list) and isinstance(update_data_converted, list):
                if len(conditions) != len(update_data_converted):
                    raise ValueError("Conditions and update data lists must have the same length")

                for cond, data in zip(conditions, update_data_converted):
                    sql, params = self._build_update_query(cond, data)
                    cursor.execute(sql, params)
                    affected_rows += cursor.rowcount

            # 单条更新模式
            else:
                if isinstance(conditions, list) or isinstance(update_data_converted, list):
                    raise ValueError("Mixed single/batch update parameters")

                sql, params = self._build_update_query(conditions, update_data_converted)
                cursor.execute(sql, params)
                affected_rows = cursor.rowcount

            conn.commit()
            return affected_rows
        except Exception as e:
            conn.rollback()
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_UPDATE', 'mysql')
            return 0
        finally:
            cursor.close()

    def _build_update_query(self, conditions: Dict, update_data: Dict) -> tuple[str, list]:
        """构建UPDATE语句"""
        with self._query_lock:
            # SET部分
            set_parts = []
            set_params = []
            for field, value in update_data.items():
                set_parts.append(f"{field} = %s")
                set_params.append(value)

            # WHERE部分
            where_parts = []
            where_params = []
            for field, condition in conditions.items():
                if isinstance(condition, dict):
                    operator = condition['opt'].upper()
                    value = condition['val']
                    where_parts.append(f"{field} {operator} %s")
                    where_params.append(value)
                else:
                    where_parts.append(f"{field} = %s")
                    where_params.append(condition)

            where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
            sql = f"UPDATE {self._table} SET {', '.join(set_parts)} WHERE {where_clause}"
            self.logger.info({"sql": sql.strip(), "params": set_params + where_params}, 'DB_SQL_UPDATE', 'mysql')
            return sql, set_params + where_params

    @with_connection
    def insert(self, conn, insert_data: Union[Dict, List[Dict]]) -> int:
        """
        插入单条或多条数据
        :param insert_data: 单条数据字典或多条数据列表
        :return: 插入成功的记录数
        """
        if not self._table:
            raise ValueError("No table specified")

        cursor = conn.cursor()
        insert_data = Attr.convert_to_json_string(insert_data)

        try:
            # 单条插入
            if isinstance(insert_data, dict):
                columns = ', '.join(insert_data.keys())
                placeholders = ', '.join(['%s'] * len(insert_data))
                values = list(insert_data.values())

                sql = f"INSERT INTO {self._table} ({columns}) VALUES ({placeholders})"
                self.logger.info({"sql": sql.strip(), "params": values}, 'DB_SQL_INSERT', 'mysql')
                cursor.execute(sql, values)
                inserted_rows = cursor.lastrowid

            # 批量插入
            elif isinstance(insert_data, list) and all(isinstance(item, dict) for item in insert_data):
                if not insert_data:
                    return 0

                insert_data = [Attr.convert_to_json_string(d) for d in insert_data]
                # 所有字典的键必须相同
                first_keys = set(insert_data[0].keys())
                if not all(set(item.keys()) == first_keys for item in insert_data):
                    raise ValueError("All dictionaries in the list must have the same keys")

                columns = ', '.join(insert_data[0].keys())
                placeholders = ', '.join(['%s'] * len(first_keys))
                value_groups = [tuple(item.values()) for item in insert_data]

                sql = f"INSERT INTO {self._table} ({columns}) VALUES ({placeholders})"
                self.logger.info({"sql": sql.strip(), "params": value_groups}, 'DB_SQL_INSERT', 'mysql')
                cursor.executemany(sql, value_groups)
                inserted_rows = cursor.lastrowid

            else:
                raise TypeError("insert_data must be a dictionary or a list of dictionaries")

            conn.commit()
            return inserted_rows
        except Exception as e:
            conn.rollback()
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_INSERT', 'mysql')
            return 0
        finally:
            cursor.close()

    @with_connection
    def delete(self, conn, conditions: Dict) -> int:
        """
        删除记录
        :param conditions: 条件字典
        :return: 受影响的行数
        """
        if not self._table:
            raise ValueError("No table specified")

        cursor = conn.cursor()
        try:
            # 构建WHERE条件
            where_parts = []
            params = []
            for field, condition in conditions.items():
                if isinstance(condition, dict):
                    operator = condition['opt'].upper()
                    value = condition['val']
                    if 'STR' == operator:
                        where_parts.append(f"{field} {value}")
                    else:
                        where_parts.append(f"{field} {operator} %s")
                        params.append(value)
                else:
                    where_parts.append(f"{field} = %s")
                    params.append(condition)

            where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
            sql = f"DELETE FROM {self._table} WHERE {where_clause}"
            self.logger.info({"sql": sql.strip(), "params": params}, 'DB_SQL_DELETE', 'mysql')

            cursor.execute(sql, params)
            affected_rows = cursor.rowcount
            conn.commit()
            return affected_rows
        except Exception as e:
            conn.rollback()
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_DELETE', 'mysql')
            return 0
        finally:
            cursor.close()

    def get_info(self, pid):
        """根据主键获取第一条记录"""
        return self.where({"id": pid}).first()

    def get_count(self, where):
        """获取总条数"""
        info = (self.where(where)
                .select(['count(1) as count'])
                .first())
        return info['count'] if info else 0

    def clear_history(self, save_count=100000):
        """清除历史数据"""
        ret = self.query_sql(f'SELECT max(id) AS mid FROM {self._table}')
        if not ret:
            return False
        mid = int(ret[0]['mid'])
        if not mid or mid <= save_count:
            return 0
        return self.delete({'id': {'opt': '<=', 'val': mid - save_count}})

class QueryState(threading.local):
    """线程/协局局部存储的查询状态"""

    _table = None

    def __init__(self, table):
        super().__init__()
        self._table = table
        self.reset()

    def reset(self):
        self._select = ['*']
        self._wheres = []
        self._where_ins = []
        self._where_sqls = []
        self._order_str = None
        self._limit_offset = None
        self._limit_count = None
