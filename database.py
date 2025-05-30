import sqlite3
from sqlite3 import Error
from datetime import date
from typing import List, Tuple, Optional

class TaskManagerDB:
    def __init__(self, db_file: str = "task_manager1.db"):
        self.conn = None
        try:
            # 创建数据库连接
            self.conn = sqlite3.connect(db_file)
            self.conn.execute("PRAGMA foreign_keys = ON")  # 启用外键约束
            print(f"成功连接到SQLite数据库: {db_file}")
            self._create_tables()
        except Error as e:
            print(f"连接数据库失败: {e}")
            raise

    def _execute_sql(self, sql: str, params: Tuple = None) -> sqlite3.Cursor:
        """执行SQL语句的通用方法"""
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            self.conn.commit()
            return cursor
        except Error as e:
            self.conn.rollback()
            print(f"执行SQL失败: {e}\nSQL: {sql}")
            raise

    def _create_tables(self):
        """创建数据库表结构"""
        tables = [
            # 任务表
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT '未开始'
                    CHECK (status IN ('未开始', '进行中', '已完成', '已中断', '已归档')),
                due_date DATE NOT NULL,
                expected_income DECIMAL(10,2) CHECK (expected_income >= 0),
                actual_income DECIMAL(10,2) CHECK (actual_income >= 0),
                expense DECIMAL(10,2) CHECK (expense >= 0),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # 标签表
            """
            CREATE TABLE IF NOT EXISTS tags (
                tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT NOT NULL UNIQUE,
                color TEXT
            )
            """,
            # 任务-标签关联表
            """
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (task_id, tag_id),
                FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
            )
            """
        ]

        # 创建索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)"
        ]

        try:
            cursor = self.conn.cursor()
            for table_sql in tables:
                cursor.execute(table_sql)
            for index_sql in indexes:
                cursor.execute(index_sql)
            self.conn.commit()
            print("数据库表结构创建成功")
        except Error as e:
            self.conn.rollback()
            print(f"创建表失败: {e}")
            raise

    # ---------- 基础操作方法 ----------
    def create_task(self, 
                   name: str, 
                   due_date: date,
                   description: str = None,
                   expected_income: float = None,
                   tags: List[str] = None) -> int:
        """创建新任务并关联标签"""
        sql = """
        INSERT INTO tasks (name, description, due_date, expected_income)
        VALUES (?, ?, ?, ?)
        """
        params = (name, description, due_date.isoformat(), expected_income)
        
        try:
            cursor = self._execute_sql(sql, params)
            task_id = cursor.lastrowid
            
            if tags:
                self._link_tags_to_task(task_id, tags)
                
            return task_id
        except Error:
            return -1

    def _link_tags_to_task(self, task_id: int, tags: List[str]):
        """为任务关联标签（内部方法）"""
        for tag_name in tags:
            # 获取或创建标签
            tag_id = self.get_or_create_tag(tag_name)
            sql = "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)"
            self._execute_sql(sql, (task_id, tag_id))

    def get_or_create_tag(self, tag_name: str, color: str = None) -> int:
        """获取或创建标签"""
        # 尝试获取现有标签
        tag_id = self.get_tag_id(tag_name)
        if tag_id is not None:
            return tag_id
            
        # 创建新标签
        sql = "INSERT INTO tags (tag_name, color) VALUES (?, ?)"
        params = (tag_name, color)
        cursor = self._execute_sql(sql, params)
        return cursor.lastrowid

    def get_tag_id(self, tag_name: str) -> Optional[int]:
        """根据标签名称获取ID"""
        sql = "SELECT tag_id FROM tags WHERE tag_name = ?"
        cursor = self._execute_sql(sql, (tag_name,))
        result = cursor.fetchone()
        return result[0] if result else None

    # ---------- 查询方法 ----------
    def get_task_details(self, task_id: int) -> dict:
        """获取任务详情（含标签）"""
        # 获取任务基本信息
        task_sql = "SELECT * FROM tasks WHERE task_id = ?"
        cursor = self._execute_sql(task_sql, (task_id,))
        task = cursor.fetchone()
        
        if not task:
            return None

        # 获取关联标签
        tag_sql = """
        SELECT t.tag_name 
        FROM task_tags tt
        JOIN tags t ON tt.tag_id = t.tag_id
        WHERE tt.task_id = ?
        """
        cursor = self._execute_sql(tag_sql, (task_id,))
        tags = [row[0] for row in cursor.fetchall()]

        # 转换为字典
        columns = [col[0] for col in cursor.description]
        return {
            **dict(zip(columns, task)),
            "tags": tags
        }

    # ---------- 统计方法 ----------
    def get_financial_summary(self) -> dict:
        """获取财务汇总数据"""
        sql = """
        SELECT 
            SUM(expected_income) AS total_expected,
            SUM(actual_income) AS total_actual,
            SUM(expense) AS total_expense
        FROM tasks
        """
        cursor = self._execute_sql(sql)
        result = cursor.fetchone()
        return {
            "total_expected": result[0] or 0,
            "total_actual": result[1] or 0,
            "total_expense": result[2] or 0
        }

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("数据库连接已关闭")

# 使用示例
""" if __name__ == "__main__":
    db = TaskManagerDB()

    # 创建测试任务
    task_id = db.create_task(
        name="DDG防晒",
        due_date=date(2025, 5, 31),
        description="图文",
        expected_income=800.00,
        tags=["黑柴狗中狗"]
    )

    # 查询任务详情
    task = db.get_task_details(task_id)
    print(f"任务详情:\n{task}")

    # 获取财务统计
    finance = db.get_financial_summary()
    print(f"\n财务统计:")
    print(f"预期收入: {finance['total_expected']}")
    print(f"实际收入: {finance['total_actual']}")
    print(f"总支出: {finance['total_expense']}")

    db.close() """