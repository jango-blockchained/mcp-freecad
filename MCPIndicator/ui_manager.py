from connection_status_dialog import ConnectionStatusDialog

class UIManager:
    def __init__(self, config_manager, process_manager, status_checker, path_finder):
        # ... existing code ...
        # Add Show Connection Status action to main menu
        if hasattr(self, 'main_menu_actions'):
            self.main_menu_actions['show_conn_status'] = QtWidgets.QAction("Show Connection Status")
            self.main_menu_actions['show_conn_status'].triggered.connect(self._show_connection_status_dialog)
            # Insert after settings if present
            if 'settings' in self.main_menu_actions:
                idx = list(self.main_menu_actions).index('settings') + 1
                actions = list(self.main_menu_actions.items())
                actions.insert(idx, ('show_conn_status', self.main_menu_actions['show_conn_status']))
                self.main_menu_actions = dict(actions)
        # Add to menu bar if not already
        if hasattr(self, 'control_button') and self.control_button and self.control_button.menu():
            self.control_button.menu().addAction(self.main_menu_actions['show_conn_status'])
        # ... existing code ...

    def _show_connection_status_dialog(self):
        dlg = ConnectionStatusDialog(self.status_checker.fc_connection_manager, self.status_checker.mcp_connection_manager)
        dlg.exec_()
