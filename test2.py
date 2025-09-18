import logging

logging.debug("hello world")
logging.debug("Byee world")

class Test:
    def test_logging(self):
        logging.info("This is test log")
        assert True
        
    def test_another_logging(self):
        logging.info("Another test log")
        
    def test_no_logging(self):
        logging.info("This is not a test log")
        
        
        