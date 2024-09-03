'''
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QWidget

class TableWidgetDemo(QWidget):
    def __init__(self):
        super().__init__()

        self.table_widget = QTableWidget(4, 4)
        for row in range(4):
            for column in range(4):
                item = QTableWidgetItem(f"Item {row},{column}")
                self.table_widget.setItem(row, column, item)

        # Make the QTableWidget read-only
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set the selection behavior to select entire rows
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)

        # Hide the column headers (horizontal headers)
        self.table_widget.horizontalHeader().setVisible(False)

        # Hide the row headers (vertical headers)
        self.table_widget.verticalHeader().setVisible(False)

        self.table_widget.itemClicked.connect(self.on_item_clicked)

        # Button to change the content of a specific item
        self.change_button = QPushButton("Change Content of Row 1, Column 2")
        self.change_button.clicked.connect(self.change_item_content)

        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addWidget(self.change_button)
        self.setLayout(layout)

    def on_item_clicked(self, item):
        print(f"Clicked on: {item.text()} at Row: {item.row()}, Column: {item.column()}")

    def change_item_content(self):
        row = 1  # Second row (index 1)
        column = 2  # Third column (index 2)

        # Access the item at the specified position
        item = self.table_widget.item(row, column)
        if item:
            # Change the text of the item
            item.setText("New Content")

if __name__ == "__main__":
    app = QApplication([])
    demo = TableWidgetDemo()
    demo.show()
    app.exec_()


from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QLabel

class TableWidgetDemo(QWidget):
    def __init__(self):
        super().__init__()

        # Create QTableWidget with 4 rows and 4 columns
        self.table_widget = QTableWidget(4, 4)
        for row in range(4):
            for column in range(4):
                item = QTableWidgetItem(f"Item {row},{column}")
                self.table_widget.setItem(row, column, item)

        # Create a label to display the selected row
        self.label = QLabel("Selected Row: None")

        # Connect the itemSelectionChanged signal to the custom slot
        self.table_widget.itemSelectionChanged.connect(self.on_selection_changed)

        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def on_selection_changed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()
        
        if selected_row != -1:  # -1 means no row is selected
            self.label.setText(f"Selected Row: {selected_row}")
        else:
            self.label.setText("Selected Row: None")

if __name__ == "__main__":
    app = QApplication([])
    demo = TableWidgetDemo()
    demo.show()
    app.exec_()
'''

from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, QLabel

class TableWidgetDemo(QWidget):
    def __init__(self):
        super().__init__()

        # Create QTableWidget with 4 rows and 4 columns
        self.table_widget = QTableWidget(4, 4)
        for row in range(4):
            for column in range(4):
                item = QTableWidgetItem(f"Item {row},{column}")
                self.table_widget.setItem(row, column, item)

        # Make the QTableWidget read-only
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set the selection behavior to select entire rows
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)

        # Hide the column headers (horizontal headers)
        self.table_widget.horizontalHeader().setVisible(False)

        # Hide the row headers (vertical headers)
        self.table_widget.verticalHeader().setVisible(False)

        # Create a button to select the second row
        select_row_button = QPushButton("Select Row 2")
        select_row_button.clicked.connect(self.select_row)

        # Button to delete a specific row
        delete_button = QPushButton("Delete Row 2")
        delete_button.clicked.connect(self.delete_row)

                # Button to change the content of a specific item
        change_button = QPushButton("Change Content of Row 1, Column 2")
        change_button.clicked.connect(self.change_item_content)

        # Create a label to display the selected row
        self.label = QLabel("Selected Row: None")

        # Connect the itemSelectionChanged signal to the custom slot
        self.table_widget.itemSelectionChanged.connect(self.on_selection_changed)



        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addWidget(select_row_button)
        layout.addWidget(delete_button)
        layout.addWidget(change_button)
        layout.addWidget(self.label)

        self.setLayout(layout)

        self.table_widget.itemClicked.connect(self.on_item_clicked)

    def change_item_content(self):
        row = 1  # Second row (index 1)
        column = 2  # Third column (index 2)

        # Access the item at the specified position
        item = self.table_widget.item(row, column)
        if item:
            # Change the text of the item
            item.setText("New Content")

    def delete_row(self):
        row_to_delete = 2  # For example, delete the third row (index 2)
        self.table_widget.removeRow(row_to_delete)

    def on_item_clicked(self, item):
        print(f"Clicked on: {item.text()} at Row: {item.row()}, Column: {item.column()}")

    def select_row(self):
        # Select the second row (index 1, because indexes are 0-based)
        self.table_widget.selectRow(1)

    def on_selection_changed(self):
        # Get the index of the current selected row
        selected_row = self.table_widget.currentRow()
        
        if selected_row != -1:  # -1 means no row is selected
            self.label.setText(f"Selected Row: {selected_row}")
        else:
            self.label.setText("Selected Row: None")

if __name__ == "__main__":
    app = QApplication([])
    demo = TableWidgetDemo()
    demo.show()
    app.exec_()