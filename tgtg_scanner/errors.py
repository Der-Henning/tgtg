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
        self.message = (
            f"Unrecognized variable {variable}. For details see "
            f"https://github.com/Der-Henning/tgtg/wiki/Configuration#variables"
        )
        super().__init__(self.message)


class TGTGConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid TGTG configuration"):
        self.message = message
        super().__init__(self.message)


class AppriseConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid Apprise configuration"):
        self.message = message
        super().__init__(self.message)


class ConsoleConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid Console configuration"):
        self.message = message
        super().__init__(self.message)


class IFTTTConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid IFTTT configuration"):
        self.message = message
        super().__init__(self.message)


class NtfyConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid NTFY configuration"):
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


class ScriptConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid Script configuration"):
        self.message = message
        super().__init__(self.message)


class LocationConfigurationError(ConfigurationError):
    def __init__(self, message="Invalid Location configuration"):
        self.message = message
        super().__init__(self.message)
