import mysql.connector
from typing import Union, List, Dict, Optional, Any
from tool.core import Logger, Error, Config


class MysqlBaseModel:
    """
    Mysql db handler
    ### Usage examples
      **> Query classes**
         # Initialize the database connection
          db = MysqlBaseModel('localhost', 'user', 'password', 'database')
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

    def __init__(self, host: str, user: str, password: str, database: str):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.logger = Logger()
        self.connection = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self._table = None
        self._reset_query()

    def _reset_query(self):
        self._table = None
        self._select = ['*']
        self._wheres = []
        self._where_ins = []
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

        # LIMIT part
        limit_clause = ''
        if self._limit_count is not None:
            if self._limit_offset is not None:
                limit_clause = f"LIMIT {self._limit_offset}, {self._limit_count}"
            else:
                limit_clause = f"LIMIT {self._limit_count}"

        sql = f"SELECT {select_clause} FROM {self._table} WHERE {where_clause} {limit_clause}"
        self.logger.info({"sql": sql.strip(), "params": params}, 'DB_SQL', 'mysql')
        return sql.strip(), params

    def get(self) -> List[Dict]:
        sql, params = self._build_query()
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        results = cursor.fetchall()
        self._reset_query()
        return results

    def first(self) -> Optional[Dict]:
        self.limit(0, 1)
        results = self.get()
        return results[0] if results else None

    def query_sql(self, sql: str) -> List[Dict]:
        """Execute a query SQL statement"""
        cursor = self.connection.cursor(dictionary=True)
        try:
            self.logger.info({"sql": sql.strip(), "params": {}}, 'DB_SQL_QUERY', 'mysql')
            cursor.execute(sql)
            if sql.lstrip().upper().startswith('SELECT'):
                return cursor.fetchall()
            return []
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

    def __del__(self):
        if hasattr(self, 'connection'):
            self.connection.close()

    def update(self, conditions: Union[Dict, List[Dict]], update_data: Union[Dict, List[Dict]]) -> int:
        """
        Update records (supports single and batch updates)
        :param conditions: Condition dictionary or list of condition dictionaries
        :param update_data: Update data dictionary or list of update data dictionaries
        :return: Number of affected rows
        """
        if not self._table:
            raise ValueError("No table specified")

        cursor = self.connection.cursor()
        affected_rows = 0

        try:
            # Batch update mode
            if isinstance(conditions, list) and isinstance(update_data, list):
                if len(conditions) != len(update_data):
                    raise ValueError("Conditions and update data lists must have the same length")

                for cond, data in zip(conditions, update_data):
                    sql, params = self._build_update_query(cond, data)
                    cursor.execute(sql, params)
                    affected_rows += cursor.rowcount

            # Single update mode
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
