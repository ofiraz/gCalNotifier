# Following https://www.pythonguis.com/tutorials/qtableview-modelviews-numpy-pandas/

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])

class TableWindow(QtWidgets.QMainWindow):
    def __init__(self, data):
        super().__init__()

        self.table = QtWidgets.QTableView()

        self.model = TableModel(data)
        self.table.setModel(self.model)

        total_column_width = self.resize_table_columns_to_contents()

        self.setFixedWidth(total_column_width + 50)

        self.setCentralWidget(self.table)

    def resize_table_columns_to_contents(self):
        header = self.table.horizontalHeader()

        total_column_width = 0

        for col in range(self.model.columnCount(0)):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
            total_column_width += self.table.columnWidth(col)

        return(total_column_width)
            