import logging

logging.debug("hello world")
logging.debug("Byee world")

class Test:
    def test_logging(self):
        logging.info("This is a test log")
        assert True
        
    def test_another_logging(self):
        logging.info("Another test log")
        assert True
        
    def test_no_logging(self):
        assert True
        