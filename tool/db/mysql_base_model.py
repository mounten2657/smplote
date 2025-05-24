import time
import threading
import mysql.connector
from typing import Union, List, Dict, Optional, Any
from tool.core import Logger, Error, Config, Attr
from mysql.connector import pooling

_mysql_pool = None
_pool_lock = threading.Lock()


class MysqlBaseModel:
    """
    Mysql db handler
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

    _db_config = Config.mysql_db_config()
    _table = None   # 表名，子类继承时指定

    def __init__(self):
        self.logger = Logger()
        self.connection = self._get_connection()
        self.prefix = self._db_config['prefix']
        self._table = self.prefix + self._table
        self._reset_query()

    def _get_connection(self):
        """获取线程安全的数据库连接"""
        global _mysql_pool

        # 双重检查锁定初始化连接池
        if _mysql_pool is None:
            with _pool_lock:
                if _mysql_pool is None:
                    self.logger.warning("----Initializing MySQL connection pool----", 'DB_CONN', 'mysql')
                    _mysql_pool = pooling.MySQLConnectionPool(
                        pool_name="smplote_pool",
                        pool_size=self._db_config['pool_size'],
                        host=self._db_config['host'],
                        port=self._db_config['port'],
                        user=self._db_config['user'],
                        password=self._db_config['password'],
                        database=self._db_config['database'],
                        connect_timeout=self._db_config['connect_timeout'],
                        autocommit=False,
                        pool_reset_session=True
                    )

        # 从连接池获取连接
        try:
            conn = _mysql_pool.get_connection()
            if not conn.is_connected():
                conn.reconnect(attempts=3, delay=1)
            return conn
        except mysql.connector.Error as e:
            self.logger.error(f"Failed to get DB connection: {e}", 'DB_CONN', 'mysql')
            raise

    def _release_connection(self, conn):
        """安全释放连接回连接池"""
        try:
            if conn.is_connected():
                conn.close()
        except Exception as e:
            self.logger.warning(f"Error releasing connection: {str(e)}", 'DB_CONN', 'mysql')

    def _reset_query(self):
        self._select = ['*']
        self._wheres = []
        self._where_ins = []
        self._where_sqls = []
        self._limit_offset = None
        self._limit_count = None

    def table(self, table_name: str) -> 'MysqlBaseModel':
        self._table = table_name
        return self

    def select(self, columns: List[str]) -> 'MysqlBaseModel':
        self._select = columns
        return self

    def where(self, conditions: Dict) -> 'MysqlBaseModel':
        for field, condition in conditions.items():
            if isinstance(condition, dict):
                operator = condition['opt'].upper()
                value = condition['val']
                self._wheres.append((field, operator, value))
            else:
                self._wheres.append((field, '=', condition))
        return self

    def where_in(self, key: str, values: List[Any]) -> 'MysqlBaseModel':
        """IN condition query method"""
        if values:
            self._where_ins.append((key, values))
        return self

    def where_sql(self, sql: str) -> 'MysqlBaseModel':
        """custom sql condition query method"""
        if sql:
            self._where_sqls.append(sql)
        return self

    def limit(self, offset: int, count: int) -> 'MysqlBaseModel':
        self._limit_offset = offset
        self._limit_count = count
        return self

    def _build_query(self) -> tuple:
        if not self._table:
            raise ValueError("No table specified")

        # SELECT part
        select_clause = ', '.join(self._select)

        # WHERE part
        where_parts = []
        params = []

        # Process ordinary WHERE conditions
        for field, operator, value in self._wheres:
            if operator == 'IN':
                placeholders = ', '.join(['%s'] * len(value))
                where_parts.append(f"{field} IN ({placeholders})")
                params.extend(value)
            else:
                where_parts.append(f"{field} {operator} %s")
                params.append(value)

        # Process WHERE IN conditions
        for field, values in self._where_ins:
            placeholders = ', '.join(['%s'] * len(values))
            where_parts.append(f"{field} IN ({placeholders})")
            params.extend(values)

        where_clause = ' AND '.join(where_parts) if where_parts else '1=1'

        for values in self._where_sqls:
            where_clause += f" {values} "

        # LIMIT part
        limit_clause = ''
        if self._limit_count is not None:
            if self._limit_offset is not None:
                limit_clause = f"LIMIT {self._limit_offset}, {self._limit_count}"
            else:
                limit_clause = f"LIMIT {self._limit_count}"

        sql = f"SELECT {select_clause} FROM {self._table} WHERE {where_clause} {limit_clause}"
        self.logger.debug({"sql": sql.strip(), "params": params}, 'DB_SQL_SELECT', 'mysql')
        return sql.strip(), params

    def get(self) -> List[Dict]:
        sql, params = self._build_query()
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        results = cursor.fetchall()
        self._reset_query()
        results = Attr.convert_to_json_dict(results)
        return results

    def first(self) -> Optional[Dict]:
        self.limit(0, 1)
        results = self.get()
        return results[0] if results else None

    def _execute_with_retry(self, operation, max_retries=3, *args, **kwargs):
        """带重试机制的数据库操作"""
        last_exception = None
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except (mysql.connector.Error, AttributeError) as e:
                last_exception = e
                if "Connection" in str(e) or not self.connection.is_connected():
                    self.logger.warning(f"DB connection error (attempt {attempt + 1}): {e}", 'DB_CONN', 'mysql')
                    try:
                        self.connection.reconnect(attempts=1, delay=1)
                    except:
                        self.connection = self._get_connection()
                time.sleep(0.5 * (attempt + 1))

        self.logger.error(f"DB operation failed after {max_retries} attempts: {last_exception}", 'DB_CONN', 'mysql')
        raise last_exception

    def query_sql(self, sql: str) -> List[Dict]:
        """Execute a query SQL statement"""

        def _query():
            cursor = self.connection.cursor(dictionary=True)
            try:
                self.logger.debug({"sql": sql.strip(), "params": {}}, 'DB_SQL_QUERY', 'mysql')
                cursor.execute(sql)
                if sql.lstrip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                return []
            finally:
                cursor.close()

        try:
            return self._execute_with_retry(_query)
        except Exception as e:
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_QUERY_SQL', 'mysql')
            return []
        finally:
            self._reset_query()

    def exec_sql(self, sql: str) -> bool:
        """Execute a non-query SQL statement"""
        cursor = self.connection.cursor()
        try:
            self.logger.info({"sql": sql.strip(), "params": {}}, 'DB_SQL_EXEC', 'mysql')
            cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_EXEC_SQL', 'mysql')
            return False
        finally:
            self._reset_query()

    def update(self, conditions: Union[Dict, List[Dict]], update_data: Union[Dict, List[Dict]]) -> int:
        """
        Update records (supports single and batch updates)
        :param conditions: Condition dictionary or list of condition dictionaries
        :param update_data: Update data dictionary or list of update data dictionaries
        :return: Number of affected rows
        """
        if not self._table:
            raise ValueError("No table specified")

        def _update():
            cursor = self.connection.cursor()
            try:
                update_data_converted = Attr.convert_to_json_string(update_data)
                affected_rows = 0

                # Batch update mode
                if isinstance(conditions, list) and isinstance(update_data_converted, list):
                    if len(conditions) != len(update_data_converted):
                        raise ValueError("Conditions and update data lists must have the same length")

                    for cond, data in zip(conditions, update_data_converted):
                        sql, params = self._build_update_query(cond, data)
                        cursor.execute(sql, params)
                        affected_rows += cursor.rowcount

                # Single update mode
                else:
                    if isinstance(conditions, list) or isinstance(update_data_converted, list):
                        raise ValueError("Mixed single/batch update parameters")

                    sql, params = self._build_update_query(conditions, update_data_converted)
                    cursor.execute(sql, params)
                    affected_rows = cursor.rowcount

                self.connection.commit()
                return affected_rows
            except:
                self.connection.rollback()
                raise
            finally:
                cursor.close()

        try:
            return self._execute_with_retry(_update)
        except Exception as e:
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_UPDATE', 'mysql')
            return 0
        finally:
            self._reset_query()

    def _build_update_query(self, conditions: Dict, update_data: Dict) -> tuple[str, list]:
        """Build an UPDATE statement"""
        # SET part
        set_parts = []
        set_params = []
        for field, value in update_data.items():
            set_parts.append(f"{field} = %s")
            set_params.append(value)

        # WHERE part
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

    def insert(self, insert_data: Union[Dict, List[Dict]]) -> int:
        """
        添加单条或多条数据
        :param insert_data: 单条数据字典或多条数据列表
        :return: 插入成功的记录数
        """
        if not self._table:
            raise ValueError("No table specified")

        cursor = self.connection.cursor()
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

                # 所有字典的键必须相同
                first_keys = set(insert_data[0].keys())
                if not all(set(item.keys()) == first_keys for item in insert_data):
                    raise ValueError("All dictionaries in the list must have the same keys")

                columns = ', '.join(first_keys)
                placeholders = ', '.join(['%s'] * len(first_keys))
                value_groups = [tuple(item.values()) for item in insert_data]

                sql = f"INSERT INTO {self._table} ({columns}) VALUES ({placeholders})"
                self.logger.info({"sql": sql.strip(), "params": value_groups}, 'DB_SQL_INSERT', 'mysql')
                cursor.executemany(sql, value_groups)
                inserted_rows = cursor.lastrowid

            else:
                raise TypeError("add_data must be a dictionary or a list of dictionaries")

            self.connection.commit()
            return inserted_rows

        except Exception as e:
            self.connection.rollback()
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_INSERT', 'mysql')
            return 0
        finally:
            self._reset_query()

    def delete(self, conditions: Dict) -> int:
        """
        Delete records
        :param conditions: Condition dictionary
        :return: Number of affected rows
        """
        if not self._table:
            raise ValueError("No table specified")

        cursor = self.connection.cursor()

        try:
            # Build WHERE conditions
            where_parts = []
            params = []
            for field, condition in conditions.items():
                if isinstance(condition, dict):
                    operator = condition['opt'].upper()
                    value = condition['val']
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
            self.connection.commit()
            return affected_rows

        except Exception as e:
            self.connection.rollback()
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_DELETE', 'mysql')
            return 0
        finally:
            self._reset_query()

    def close(self):
        """显式关闭数据库连接"""
        if hasattr(self, 'connection') and self.connection:
            self._release_connection(self.connection)
            self.logger.info("MySQL connection closed", 'DB_CONN', 'mysql')

