import os

'''
Stores all relavant file paths 
'''
class Paths:
    # /configs
    config_directory = 'configs'
    config_filename = 'config.json'
    config_filepath = os.path.join(config_directory, config_filename)

    # /orders
    orders_directory = 'orders'

    # /orders/orders.json
    order_filename = 'orders.json'
    order_filepath = os.path.join(orders_directory, order_filename)

    # /configs/dca_investment_parameter.json
    dca_filename = 'dca_investment_parameter.json'
    dca_file_path = os.path.join(config_directory, dca_filename)

    # /logs
    logs_directory = 'logs'
    default_log_filename = 'bot.log'    
    # /logs/bot_error.log - Used when log level/file is not initialized but logging is needed
    uninitialized_logger_error_file = 'bot_error.log'
    uninitialized_logger_error_file_path = os.path.join(logs_directory, uninitialized_logger_error_file)
    # /logs/bot.log 
    default_log_filepath = os.path.join(logs_directory, default_log_filename)