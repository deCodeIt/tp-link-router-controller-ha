import logging
import time
from collections.abc import Callable

from tplinkrouterc6u import TplinkRouterProvider
from tplinkrouterc6u.client_abstract import AbstractRouter

_LOGGER = logging.getLogger(__name__)


class TPLinkGatewayClient:

    def __init__(self, host: str, password: str) -> None:
        self._host = host
        self._password = password

    def _connect(self) -> AbstractRouter:
        router = TplinkRouterProvider.get_client(
            self._host, self._password, logger=_LOGGER, verify_ssl=False
        )
        router.authorize()
        return router

    def _disconnect(self, router: AbstractRouter) -> None:
        try:
            router.logout()
        except Exception:
            pass

    def get_lan_gateway(self) -> str | None:
        try:
            router = self._connect()
            try:
                config = router.request(
                    "admin/network?form=lan_ipv4",
                    "operation=read",
                )
                return config.get("lan_gw") if config else None
            finally:
                self._disconnect(router)
        except Exception:
            _LOGGER.exception("Failed to fetch LAN gateway")
            return None

    def get_dhcp_gateway(self) -> str | None:
        try:
            router = self._connect()
            try:
                config = router.request(
                    "admin/dhcps?form=setting",
                    "operation=read",
                )
                return config.get("gateway") if config else None
            finally:
                self._disconnect(router)
        except Exception:
            _LOGGER.exception("Failed to fetch DHCP gateway")
            return None

    def test_connection(self) -> tuple[bool, str]:
        try:
            router = self._connect()
            self._disconnect(router)
            return True, ""
        except Exception as ex:
            _LOGGER.exception("Router connection test failed")
            return False, str(ex)

    def set_gateway(
        self,
        lan_gateway: str,
        dhcp_gateway: str | None,
        status_cb: Callable[[str], None] | None = None,
    ) -> bool:
        def _status(s: str) -> None:
            if status_cb:
                status_cb(s)

        from .const import (
            STATUS_LOGGING_IN,
            STATUS_READING_LAN,
            STATUS_UPDATING_LAN,
            STATUS_WAITING_ROUTER,
            STATUS_READING_DHCP,
            STATUS_UPDATING_DHCP,
            STATUS_SUCCESS,
            STATUS_FAILED,
        )

        try:
            _status(STATUS_LOGGING_IN)
            router = self._connect()
        except Exception:
            _LOGGER.exception("Failed to connect to router")
            _status(STATUS_FAILED)
            return False

        try:
            _status(STATUS_READING_LAN)
            lan_config = router.request(
                "admin/network?form=lan_ipv4",
                "operation=read",
            )
            if lan_config is None:
                _status(STATUS_FAILED)
                return False

            _status(STATUS_UPDATING_LAN)
            lan_config["lan_gw"] = lan_gateway
            write_data = "&".join(f"{k}={v}" for k, v in lan_config.items())
            result = router.request(
                "admin/network?form=lan_ipv4",
                f"operation=write&{write_data}",
                ignore_response=True,
            )

            if dhcp_gateway:
                self._disconnect(router)
                _status(STATUS_WAITING_ROUTER)
                time.sleep(10)
                for attempt in range(6):
                    try:
                        router = self._connect()
                        break
                    except Exception:
                        if attempt == 5:
                            _LOGGER.error("Router not back up after LAN update")
                            _status(STATUS_FAILED)
                            return False
                        time.sleep(5)

                _status(STATUS_READING_DHCP)
                dhcp_config = router.request(
                    "admin/dhcps?form=setting",
                    "operation=read",
                )
                if dhcp_config is None:
                    _status(STATUS_FAILED)
                    return False

                _status(STATUS_UPDATING_DHCP)
                dhcp_config["gateway"] = dhcp_gateway
                write_data = "&".join(f"{k}={v}" for k, v in dhcp_config.items())
                router.request(
                    "admin/dhcps?form=setting",
                    f"operation=write&{write_data}",
                    ignore_response=True,
                )

            _status(STATUS_SUCCESS)
            return True
        except Exception:
            _LOGGER.exception("Failed during gateway update")
            _status(STATUS_FAILED)
            return False
        finally:
            self._disconnect(router)
