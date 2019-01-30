"""module contains flask application settings"""
import os

version = '1.3.1'

PROJECT_ROOT_DIR = \
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
APP_DIR = os.path.join(PROJECT_ROOT_DIR, 'ppp_web')
BIN_DIR = os.path.join(APP_DIR, 'bin')


class Config:
    """Base configuration."""
    WKHTMLTOPDF_PATH_LOCAL = os.path.join(BIN_DIR, 'wkhtmltopdf')
    WKHTMLTOPDF_PATH_SYSTEM = \
        os.getenv('WKHTMLTOPDF_PATH_SYSTEM', 'wkhtmltopdf')

    THREADS_PER_PAGE = 2
    CSRF_ENABLED = True
    CSRF_SESSION_KEY = "?x1234567890x!"  # TODO: To env.
    SECRET_KEY = "!x1234567890x?"  # TODO: To env.
    DEBUG = False
    TESTING = False


class StagingConfig(Config):
    """Production configuration."""
    DEBUG = True
    TESTING = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'staging': StagingConfig,
    'default': DevelopmentConfig
}
