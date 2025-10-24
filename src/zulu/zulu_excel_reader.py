# https://bitbucket.org/openpyxl/openpyxl
# https://openpyxl.readthedocs.io/en/stable/
import openpyxl

TAG_TABLE_COLUMNS = 'Navigation>'
TAG_TABLE_ROW = 'Navigation:'
TAG_ENTRY_ROW = ':'
TAG_HYPHEN = '-'
TAG_EMPTY = ''
COLUMN_TAG = 1  # BaseDir:
COLUMN_NAME = 2 # Folder:
COLUMN_FIRST_CULUMN = 3

class ExcelReaderExecption(Exception):
  pass

def _get_cell_value(obj_row, index):
  '''TODO: This method is duplicated'''
  if index >= len(obj_row):
    return ''

  v = obj_row[index]
  if v.value == None:
    return ''

  return str(v.value)

class Entry:
  def __init__(self, str_tag_cell, str_name_cell, obj_row):
    self.str_tag_cell = str_tag_cell
    self.str_name_cell = str_name_cell
    self.obj_row = obj_row

  def columns(self):
    d = {
      'tag': _get_cell_value(self.obj_row, COLUMN_NAME),
      'a': _get_cell_value(self.obj_row, COLUMN_FIRST_CULUMN),
    }
    b = _get_cell_value(self.obj_row, COLUMN_FIRST_CULUMN+1)
    if b != '':
      d['b'] = b
    return d

  def columns_obsolete(self):
    list_columns = []
    for i in range(COLUMN_FIRST_CULUMN, len(self.obj_row)):
      obj_column = self.obj_row[i]
      if obj_column is None:
        break
      str_column = obj_column.value
      if str_column is None:
        break
      list_columns.append(str_column)
    return list_columns

  def dump(self):
    print('entry: {} {}: {}'.format(self.str_tag_cell, self.str_name_cell, self.obj_row))

class Table:
  def __init__(self, str_table_name):
    self.str_table_name = str_table_name
    self.list_rows = []
    self.dict_columns = {}

  def parse_columns(self, obj_row):
    for i in range(COLUMN_FIRST_CULUMN, len(obj_row)):
      column_name = _get_cell_value(obj_row, i).strip()
      if column_name == TAG_HYPHEN:
        continue
      if column_name == TAG_EMPTY:
        break
      self.dict_columns[column_name] = i

  def parse_row(self, obj_row):
    str_name_cell = _get_cell_value(obj_row, COLUMN_NAME)
    assert str_name_cell == self.str_table_name
    self.list_rows.append(obj_row)

  def get_row_as_dict(self, obj_row):
    d = {}
    for str_column_name, i_column in self.dict_columns.items():
      str_column_value = _get_cell_value(obj_row, i_column)
      d[str_column_name] = str_column_value
    return d

  def dump(self, obj_file):
    print('table: {}'.format(self.str_table_name), file=obj_file)
    print('columns: {}'.format(sorted(self.dict_columns.items())), file=obj_file)
    for obj_row in self.list_rows:
      print('row: {}'.format(self.get_row_as_dict(obj_row)), file=obj_file)

  def raise_exception(self, str_msg):
    raise ExcelReaderExecption('Table "{}": {}'.format(self.str_table_name, str_msg), file=obj_file)

class ExcelReader:
  def __init__(self, str_filename_xlsx):
    self.str_filename_xlsx = str_filename_xlsx
    self.dict_tables = {}
    obj_actual_table = None
    self.dict_entries = {}

    objWorkbook = openpyxl.load_workbook(filename=str_filename_xlsx, read_only=True, data_only=True)
    for objWorksheet in objWorkbook.worksheets:
      # print(objWorksheet.title)
      for obj_row in objWorksheet.rows:
        if len(obj_row) < COLUMN_TAG:
          # print('EMPTY_ROW')
          obj_actual_table = None
          continue
        str_tag_cell = obj_row[COLUMN_TAG].value
        if str_tag_cell is None:
          str_tag_cell = ''
        str_name_cell = obj_row[COLUMN_NAME].value
        if str_name_cell is None:
          str_name_cell = ''
        str_tag_cell = str(str_tag_cell)
        str_name_cell = str(str_name_cell)

        # print('COLUMN_TAG={} COLUMN_NAME={} obj_actual_table={}'.format(str_tag_cell, str_name_cell, obj_actual_table))

        if obj_actual_table:
          if str_tag_cell == TAG_TABLE_ROW:
            obj_actual_table.parse_row(obj_row)
            continue
          if str_tag_cell == TAG_HYPHEN:
            continue
          obj_actual_table = None
          continue

        if str_tag_cell == TAG_TABLE_COLUMNS:
          if len(obj_row) < 4:
            obj_actual_table.raise_exception('Need at least 4 rows')
          str_table_name = str_name_cell
          assert str_table_name is not None
          obj_actual_table = Table(str_table_name)
          self.dict_tables[str_table_name] = obj_actual_table
          obj_actual_table.parse_columns(obj_row)
          continue
        
        if str_tag_cell.endswith(TAG_ENTRY_ROW):
          str_tag_cell = str_tag_cell[:-len(TAG_ENTRY_ROW)]
          self.add_entry(str_tag_cell, str_name_cell, obj_row)

  def add_entry(self, str_tag_cell, str_name_cell, obj_row):
    obj_entry = Entry(str_tag_cell, str_name_cell, obj_row)

    list_entries = self.dict_entries.get(str_tag_cell, None)
    if list_entries is None:
      list_entries = []
      self.dict_entries[str_tag_cell] = list_entries
    list_entries.append(obj_entry.columns())

  def dump(self, obj_file):
    for _, obj_table in self.dict_tables.items():
      obj_table.dump(obj_file)

    for str_entry, list_entries in self.dict_entries.items():
      for dict_entry in list_entries:
        print('entry: {}: {}'.format(str_entry, dict_entry), file=obj_file)

        # obj_entry.dump()


if __name__ == '__main__':
  import os
  import sys
  str_filename = os.path.join(os.path.dirname(__file__), 'zulu_structure.xlsx')
  excel = ExcelReader(str_filename)
  excel.dump(sys.stdout)
