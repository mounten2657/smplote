import sqlite3
from typing import Union, List, Dict, Optional, Any
from tool.core import Logger, Error, Config


class SqliteBaseModel:
    """
    Sqlite db handler
    ### 使用示例
      **>查询类**
         # 初始化数据库连接
          db = SqliteBaseModel('/root/sqlite/wx_app.db')  # 需要绝对路径
         # 获取单条记录
          msg_one = db.table('Msg') \
             .select(['id', 'msg']) \
             .where({
                 "wxid": "wx_x123",
                 "msg": {"opt": "like", "val": "%你好%"},
                 "create_time": {"opt": ">", "val": "2025-02-01 00:00:00"}
             }) \
             .first()
          print(msg_one)  # 输出: {"id":101,"msg":"你好世界"}

         # 获取分页列表
          msg_list = db.table('Msg') \
              .select(['id', 'msg']) \
              .where({
                  "wxid": "wx_x123",
                  "msg": {"opt": "like", "val": "%你好%"},
                  "create_time": {"opt": ">", "val": "2025-02-01 00:00:00"}
              }) \
              .limit(0, 10) \
              .get()
          print(msg_list)  # 输出: [{"id":101,"msg":"你好世界"}, ...]

      **>操作类**
         # 执行自定义查询SQL
          data = db.query_sql("SELECT id, msg FROM Msg WHERE wxid = 'wx_123' LIMIT 5")

         # 执行非查询操作（更新，删除，索引，建表等）
          success = db.exec_sql("UPDATE Msg SET status = 1 WHERE id = 101")
          if success:
              print("更新成功")

      **>更新类**
         # 更新id=100的记录
          affected = db.table('Msg').update(
              {"id": 100},
              {"remark": "u_test1", "user": "joyn1"}
          )
          print(f"更新了 {affected} 条记录")

         # 批量更新两条记录
          affected = db.table('Msg').update(
              [{"id": 100}, {"id": 102}],
              [
                  {"remark": "u_test1", "user": "joyn1"},
                  {"remark": "u_test22", "user": "joyn44"}
              ]
          )
          print(f"批量更新了 {affected} 条记录")

         # 删除wxid为wx_123且状态为0的记录
          deleted = db.table('Msg').delete({
              "wxid": "wx_123",
              "status": 0
          })
          print(f"删除了 {deleted} 条记录")

         # 使用操作符的删除
          deleted = db.table('Msg').delete({
              "create_time": {"opt": "<", "val": "2025-01-01"}
          })
          print(f"删除了 {deleted} 条旧记录")

    """

    def __init__(self, db_path: str = ''):
        # 根据自己的需求修改默认的数据库，需要绝对路径
        self.db_path = db_path if db_path else Config.db_path()
        self.logger = Logger()
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._reset_query()

    def _reset_query(self):
        self._table = None
        self._select = ['*']
        self._wheres = []
        self._where_ins = []
        self._limit_offset = None
        self._limit_count = None

    def table(self, table_name: str) -> 'SqliteBaseModel':
        self._table = table_name
        return self

    def select(self, columns: List[str]) -> 'SqliteBaseModel':
        self._select = columns
        return self

    def where(self, conditions: Dict) -> 'SqliteBaseModel':
        for field, condition in conditions.items():
            if isinstance(condition, dict):
                operator = condition['opt'].upper()
                value = condition['val']
                self._wheres.append((field, operator, value))
            else:
                self._wheres.append((field, '=', condition))
        return self

    def where_in(self, key: str, values: List[Any]) -> 'SqliteBaseModel':
        """IN条件查询方法"""
        if values:
            self._where_ins.append((key, values))
        return self

    def limit(self, offset: int, count: int) -> 'SqliteBaseModel':
        self._limit_offset = offset
        self._limit_count = count
        return self

    def _build_query(self) -> tuple:
        if not self._table:
            raise ValueError("No table specified")

        # SELECT 部分
        select_clause = ', '.join(self._select)

        # WHERE 部分
        where_parts = []
        params = []

        # 处理普通WHERE条件
        for field, operator, value in self._wheres:
            if operator == 'IN':
                placeholders = ', '.join(['?'] * len(value))
                where_parts.append(f"{field} IN ({placeholders})")
                params.extend(value)
            else:
                where_parts.append(f"{field} {operator} ?")
                params.append(value)

        # 处理WHERE IN条件
        for field, values in self._where_ins:
            placeholders = ', '.join(['?'] * len(values))
            where_parts.append(f"{field} IN ({placeholders})")
            params.extend(values)

        where_clause = ' AND '.join(where_parts) if where_parts else '1=1'

        # LIMIT 部分
        limit_clause = ''
        if self._limit_count is not None:
            limit_clause = f"LIMIT {self._limit_count}"
            if self._limit_offset is not None:
                limit_clause = f"LIMIT {self._limit_offset}, {self._limit_count}"

        sql = f"SELECT {select_clause} FROM {self._table} WHERE {where_clause} {limit_clause}"
        self.logger.info({"sql": sql.strip(), "params": params}, 'DB_SQL', 'sqlite')
        return sql.strip(), params

    def get(self) -> List[Dict]:
        sql, params = self._build_query()
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        self._reset_query()
        return results

    def first(self) -> Optional[Dict]:
        self.limit(0, 1)
        results = self.get()
        return results[0] if results else None

    def query_sql(self, sql: str) -> List[Dict]:
        """执行查询SQL语句"""
        cursor = self.connection.cursor()
        try:
            self.logger.info({"sql": sql.strip(), "params": {}}, 'DB_SQL_QUERY', 'sqlite')
            cursor.execute(sql)
            if sql.lstrip().upper().startswith('SELECT'):
                return [dict(row) for row in cursor.fetchall()]
            return []
        except Exception as e:
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_QUERY_SQL', 'sqlite')
            return []
        finally:
            self._reset_query()

    def exec_sql(self, sql: str) -> bool:
        """执行非查询SQL语句"""
        cursor = self.connection.cursor()
        try:
            self.logger.info({"sql": sql.strip(), "params": {}}, 'DB_SQL_EXEC', 'sqlite')
            cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_EXEC_SQL', 'sqlite')
            return False
        finally:
            self._reset_query()

    def __del__(self):
        if hasattr(self, 'connection'):
            self.connection.close()

    def update(self, conditions: Union[Dict, List[Dict]], update_data: Union[Dict, List[Dict]]) -> int:
        """
        更新记录（支持单条和批量更新）
        :param conditions: 条件字典或条件字典列表
        :param update_data: 更新数据字典或更新数据字典列表
        :return: 影响的行数
        """
        if not self._table:
            raise ValueError("No table specified")

        cursor = self.connection.cursor()
        affected_rows = 0

        try:
            # 批量更新模式
            if isinstance(conditions, list) and isinstance(update_data, list):
                if len(conditions) != len(update_data):
                    raise ValueError("Conditions and update data lists must have same length")

                for cond, data in zip(conditions, update_data):
                    sql, params = self._build_update_query(cond, data)
                    cursor.execute(sql, params)
                    affected_rows += cursor.rowcount

            # 单条更新模式
            else:
                if isinstance(conditions, list) or isinstance(update_data, list):
                    raise ValueError("Mixed single/batch update parameters")

                sql, params = self._build_update_query(conditions, update_data)
                cursor.execute(sql, params)
                affected_rows = cursor.rowcount

            self.connection.commit()
            return affected_rows

        except Exception as e:
            self.connection.rollback()
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_UPDATE', 'sqlite')
            return 0
        finally:
            self._reset_query()

    def _build_update_query(self, conditions: Dict, update_data: Dict) -> tuple[str, list]:
        """构建UPDATE语句"""
        # SET 部分
        set_parts = []
        set_params = []
        for field, value in update_data.items():
            set_parts.append(f"{field} = ?")
            set_params.append(value)

        # WHERE 部分
        where_parts = []
        where_params = []
        for field, condition in conditions.items():
            if isinstance(condition, dict):
                operator = condition['opt'].upper()
                value = condition['val']
                where_parts.append(f"{field} {operator} ?")
                where_params.append(value)
            else:
                where_parts.append(f"{field} = ?")
                where_params.append(condition)

        where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
        sql = f"UPDATE {self._table} SET {', '.join(set_parts)} WHERE {where_clause}"
        self.logger.info({"sql": sql.strip(), "params": set_params + where_params}, 'DB_SQL_UPDATE', 'sqlite')
        return sql, set_params + where_params

    def delete(self, conditions: Dict) -> int:
        """
        删除记录
        :param conditions: 条件字典
        :return: 影响的行数
        """
        if not self._table:
            raise ValueError("No table specified")

        cursor = self.connection.cursor()

        try:
            # 构建WHERE条件
            where_parts = []
            params = []
            for field, condition in conditions.items():
                if isinstance(condition, dict):
                    operator = condition['opt'].upper()
                    value = condition['val']
                    where_parts.append(f"{field} {operator} ?")
                    params.append(value)
                else:
                    where_parts.append(f"{field} = ?")
                    params.append(condition)

            where_clause = ' AND '.join(where_parts) if where_parts else '1=1'
            sql = f"DELETE FROM {self._table} WHERE {where_clause}"
            self.logger.info({"sql": sql.strip(), "params": params}, 'DB_SQL_DELETE', 'sqlite')

            cursor.execute(sql, params)
            affected_rows = cursor.rowcount
            self.connection.commit()
            return affected_rows

        except Exception as e:
            self.connection.rollback()
            err = Error.handle_exception_info(e)
            self.logger.exception(err, 'DB_EXP_DELETE', 'sqlite')
            return 0
        finally:
            self._reset_query()


