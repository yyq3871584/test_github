import pyodbc
import json
from datetime import datetime
from typing import Dict, List, Any


SERVER = 'your_server_address'
PORT = '1433'
DATABASE = 'your_database_name'
USERNAME = 'your_username'
PASSWORD = 'your_password'
USE_WINDOWS_AUTH = False


def create_connection() -> pyodbc.Connection:
    if USE_WINDOWS_AUTH:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER},{PORT};DATABASE={DATABASE};Trusted_Connection=yes;'
    else:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER},{PORT};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};'
    
    return pyodbc.connect(conn_str, timeout=30)


def get_tables(cursor) -> List[Dict[str, Any]]:
    query = """
    SELECT 
        t.TABLE_NAME,
        t.TABLE_TYPE,
        t.CREATE_DATE,
        t.MODIFY_DATE,
        prop.value AS TABLE_DESCRIPTION
    FROM INFORMATION_SCHEMA.TABLES t
    LEFT JOIN sys.extended_properties prop 
        ON prop.major_id = OBJECT_ID(t.TABLE_SCHEMA + '.' + t.TABLE_NAME)
        AND prop.minor_id = 0 
        AND prop.name = 'MS_Description'
    WHERE t.TABLE_TYPE IN ('BASE TABLE', 'VIEW')
    ORDER BY t.TABLE_TYPE, t.TABLE_NAME
    """
    cursor.execute(query)
    
    tables = []
    for row in cursor.fetchall():
        table_info = {
            'table_name': row.TABLE_NAME,
            'table_type': row.TABLE_TYPE,
            'schema': row.TABLE_SCHEMA if hasattr(row, 'TABLE_SCHEMA') else 'dbo',
            'create_time': str(row.CREATE_DATE) if row.CREATE_DATE else None,
            'modify_time': str(row.MODIFY_DATE) if row.MODIFY_DATE else None,
            'description': row.TABLE_DESCRIPTION if row.TABLE_DESCRIPTION else None
        }
        tables.append(table_info)
    
    return tables


def get_columns(cursor, table_name: str, schema: str) -> List[Dict[str, Any]]:
    query = """
    SELECT 
        c.COLUMN_NAME,
        c.DATA_TYPE,
        c.CHARACTER_MAXIMUM_LENGTH,
        c.NUMERIC_PRECISION,
        c.NUMERIC_SCALE,
        c.IS_NULLABLE,
        c.COLUMN_DEFAULT,
        c.COLUMN_DESCRIPTION,
        c.ORDINAL_POSITION,
        c.IS_PRIMARY_KEY
    FROM (
        SELECT 
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            prop.value AS COLUMN_DESCRIPTION,
            c.ORDINAL_POSITION,
            CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END AS IS_PRIMARY_KEY
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN sys.extended_properties prop 
            ON prop.major_id = OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME)
            AND prop.minor_id = c.ORDINAL_POSITION
            AND prop.name = 'MS_Description'
        LEFT JOIN (
            SELECT ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku 
                ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
            WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                AND ku.TABLE_NAME = ? AND ku.TABLE_SCHEMA = ?
        ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
        WHERE c.TABLE_NAME = ? AND c.TABLE_SCHEMA = ?
    ) c
    ORDER BY c.ORDINAL_POSITION
    """
    cursor.execute(query, (table_name, schema, table_name, schema))
    
    columns = []
    for row in cursor.fetchall():
        col_info = {
            'column_name': row.COLUMN_NAME,
            'data_type': row.DATA_TYPE,
            'max_length': row.CHARACTER_MAXIMUM_LENGTH,
            'precision': row.NUMERIC_PRECISION,
            'scale': row.NUMERIC_SCALE,
            'is_nullable': row.IS_NULLABLE == 'YES',
            'default_value': row.COLUMN_DEFAULT,
            'description': row.COLUMN_DESCRIPTION,
            'is_primary_key': row.IS_PRIMARY_KEY == 1,
            'ordinal_position': row.ORDINAL_POSITION
        }
        columns.append(col_info)
    
    return columns


def get_views(cursor) -> List[Dict[str, Any]]:
    query = """
    SELECT 
        v.TABLE_NAME,
        v.TABLE_SCHEMA,
        v.CREATE_DATE,
        v.MODIFY_DATE,
        prop.value AS VIEW_DESCRIPTION,
        m.definition AS VIEW_DEFINITION
    FROM INFORMATION_SCHEMA.VIEWS v
    LEFT JOIN sys.extended_properties prop 
        ON prop.major_id = OBJECT_ID(v.TABLE_SCHEMA + '.' + v.TABLE_NAME)
        AND prop.minor_id = 0 
        AND prop.name = 'MS_Description'
    LEFT JOIN sys.sql_modules m 
        ON m.object_id = OBJECT_ID(v.TABLE_SCHEMA + '.' + v.TABLE_NAME)
    ORDER BY v.TABLE_SCHEMA, v.TABLE_NAME
    """
    cursor.execute(query)
    
    views = []
    for row in cursor.fetchall():
        view_info = {
            'view_name': row.TABLE_NAME,
            'schema': row.TABLE_SCHEMA,
            'create_time': str(row.CREATE_DATE) if row.CREATE_DATE else None,
            'modify_time': str(row.MODIFY_DATE) if row.MODIFY_DATE else None,
            'description': row.VIEW_DESCRIPTION if row.VIEW_DESCRIPTION else None,
            'definition': row.VIEW_DEFINITION if row.VIEW_DEFINITION else None
        }
        views.append(view_info)
    
    return views


def get_stored_procedures(cursor) -> List[Dict[str, Any]]:
    query = """
    SELECT 
        p.name AS procedure_name,
        p.create_date,
        p.modify_date,
        prop.value AS procedure_description,
        m.definition AS procedure_definition,
        p.type_desc
    FROM sys.procedures p
    LEFT JOIN sys.extended_properties prop 
        ON prop.major_id = p.object_id
        AND prop.minor_id = 0 
        AND prop.name = 'MS_Description'
    LEFT JOIN sys.sql_modules m 
        ON m.object_id = p.object_id
    ORDER BY p.name
    """
    cursor.execute(query)
    
    procedures = []
    for row in cursor.fetchall():
        proc_info = {
            'procedure_name': row.procedure_name,
            'type': row.type_desc,
            'create_time': str(row.create_date) if row.create_date else None,
            'modify_time': str(row.modify_date) if row.modify_date else None,
            'description': row.procedure_description if row.procedure_description else None,
            'definition': row.procedure_definition if row.procedure_definition else None
        }
        procedures.append(proc_info)
    
    return procedures


def get_stored_procedure_params(cursor, proc_name: str) -> List[Dict[str, Any]]:
    query = """
    SELECT 
        p.name AS param_name,
        t.name AS data_type,
        p.max_length,
        p.precision,
        p.scale,
        p.is_output,
        p.default_value,
        p.parameter_id
    FROM sys.parameters p
    INNER JOIN sys.types t ON p.user_type_id = t.user_type_id
    WHERE p.object_id = OBJECT_ID(?)
    ORDER BY p.parameter_id
    """
    cursor.execute(query, (proc_name,))
    
    params = []
    for row in cursor.fetchall():
        param_info = {
            'parameter_name': row.param_name,
            'data_type': row.data_type,
            'max_length': row.max_length,
            'precision': row.precision,
            'scale': row.scale,
            'is_output': row.is_output,
            'default_value': row.default_value,
            'ordinal_position': row.parameter_id
        }
        params.append(param_info)
    
    return params


def get_database_info(cursor) -> Dict[str, Any]:
    query = """
    SELECT 
        name,
        compatibility_level,
        collation_name,
        create_date,
        state_desc
    FROM sys.databases
    WHERE name = DB_NAME()
    """
    cursor.execute(query)
    row = cursor.fetchone()
    
    return {
        'database_name': row.name if row else None,
        'compatibility_level': row.compatibility_level if row else None,
        'collation': row.collation_name if row else None,
        'create_date': str(row.create_date) if row and row.create_date else None,
        'state': row.state_desc if row else None
    }


def extract_full_schema() -> Dict[str, Any]:
    print('正在建立数据库连接...')
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        print('正在提取数据库基本信息...')
        db_info = get_database_info(cursor)
        
        print('正在提取表和视图信息...')
        tables = get_tables(cursor)
        
        print('正在提取字段信息...')
        for table in tables:
            table['columns'] = get_columns(cursor, table['table_name'], table['schema'])
        
        print('正在提取视图定义...')
        views = get_views(cursor)
        
        print('正在提取存储过程信息...')
        procedures = get_stored_procedures(cursor)
        
        print('正在提取存储过程参数...')
        for proc in procedures:
            full_proc_name = proc['procedure_name']
            proc['parameters'] = get_stored_procedure_params(cursor, full_proc_name)
        
        schema_data = {
            'version': '1.0',
            'extract_timestamp': datetime.now().isoformat(),
            'database': db_info,
            'tables': [t for t in tables if t['table_type'] == 'BASE TABLE'],
            'views': views,
            'stored_procedures': procedures
        }
        
        print('数据库结构提取完成！')
        return schema_data
        
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    schema_data = extract_full_schema()
    
    output_file = f"schema_{schema_data['database']['database_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(schema_data, f, ensure_ascii=False, indent=2)
    
    print(f'JSON文件已保存至: {output_file}')
    print(f'共计: {len(schema_data["tables"])} 个表, {len(schema_data["views"])} 个视图, {len(schema_data["stored_procedures"])} 个存储过程')