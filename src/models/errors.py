class Error(Exception):
    pass


class TgtgLoginError(Error):
    pass


class TgtgAPIError(Error):
    pass


class TgtgCaptchaError(TgtgAPIError):
    pass


class TgtgPollingError(TgtgAPIError):
    pass


class ConfigurationError(Error):
    pass


class MaskConfigurationError(ConfigurationError):
    def __init__(self, variable):
        self.message = f"Unrecognized variable {variable}"
        super().__init__(self.message)


class TGTGConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid TGTG configuration"):
        self.message = message
        super().__init__(self.message)


class IFTTTConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid IFTTT configuration"):
        self.message = message
        super().__init__(self.message)


class SMTPConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid SMTP configuration"):
        self.message = message
        super().__init__(self.message)


class PushSaferConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid PushSafer configuration"):
        self.message = message
        super().__init__(self.message)


class WebHookConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid Webhook configuration"):
        self.message = message
        super().__init__(self.message)


class TelegramConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid Telegram configuration"):
        self.message = message
        super().__init__(self.message)
