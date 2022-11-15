from functools import partial
from multiprocessing.connection import Client
import pytest
from onelauncher.network.game_launcher_config import GameLauncherConfig
from onelauncher.settings import ClientType


def get_mock_game_launcher_config_partial() -> partial[GameLauncherConfig]:
    return partial(
        GameLauncherConfig,
        client_win64_filename="lotroclient64.exe",
        client_win32_filename="lotroclient.exe",
        client_win32_legacy_filename="lotroclient_awesomium.exe",
        client_launch_args_template="-a {SUBSCRIPTION} -h {LOGIN} --glsticketdirect {GLS} --chatserver {CHAT} --rodat on --language {LANG} --gametype LOTRO --authserverurl {AUTHSERVERURL} --glsticketlifetime {GLSTICKETLIFETIME}",
        client_crash_server_arg="http://crash.lotro.com:8080/CrashReceiver-1.0",
        client_auth_server_arg="https://gls.lotro.com/gls.authserver/service.asmx",
        client_gls_ticket_lifetime_arg="21600",
        client_default_upload_throttle_mbps_arg="1",
        client_bug_url_arg=None,
        client_support_url_arg=None,
        client_support_service_url_arg=None,
        high_res_patch_arg=None,
        patching_product_code="LOTRO",
        login_queue_url="https://gls.lotro.com/GLS.AuthServer/LoginQueue.aspx",
        login_queue_params_template="command=TakeANumber&amp;subscription={0}&amp;ticket={1}&amp;ticket_type=GLS&amp;queue_url={2}",
        newsfeed_url_template="https://forums.lotro.com/{lang}/launcher-feed.xml")


@pytest.fixture
def mock_game_launcher_config():
    yield get_mock_game_launcher_config_partial()()


class TestGameLauncherConfig:
    # Test that get_specific_client_filename supports all client types
    @pytest.mark.parametrize("client_type", list(ClientType))
    def test_get_specific_client_filename(
            self,
            mock_game_launcher_config: GameLauncherConfig,
            client_type: ClientType):
        assert type(mock_game_launcher_config.get_specific_client_filename(
            client_type)) in [None, str]

    @pytest.mark.parametrize(["client_win64_filename",
                              "client_win32_filename",
                              "client_win32_legacy_filename",
                              "input_client_type",
                              "expected_output_client_type"],
                             [(None,
                               "lotroclient.exe",
                               "lotroclient_awesomium.exe",
                               ClientType.WIN64,
                               ClientType.WIN32),
                              ("lotroclient64.exe",
                               None,
                               "lotroclient_awesomium.exe",
                               ClientType.WIN32,
                               ClientType.WIN32_LEGACY),
                              ("lotroclient64.exe",
                               "lotroclient.exe",
                               None,
                               ClientType.WIN32_LEGACY,
                               ClientType.WIN32),
                              ("lotroclient64.exe",
                               "lotroclient.exe",
                               "lotroclient_awesomium.exe",
                               ClientType.WIN64,
                               ClientType.WIN64),
                              ("lotroclient64.exe",
                               "lotroclient.exe",
                               "lotroclient_awesomium.exe",
                               ClientType.WIN32,
                               ClientType.WIN32),
                              ("lotroclient64.exe",
                               "lotroclient.exe",
                               "lotroclient_awesomium.exe",
                               ClientType.WIN32_LEGACY,
                               ClientType.WIN32_LEGACY)
                              ])
    def test_get_client_filename(
            self,
            client_win64_filename: str,
            client_win32_filename: str,
            client_win32_legacy_filename: str,
            input_client_type: ClientType,
            expected_output_client_type: str):
        mock_game_launcher_config = get_mock_game_launcher_config_partial()(
            client_win64_filename=client_win64_filename,
            client_win32_filename=client_win32_filename,
            client_win32_legacy_filename=client_win32_legacy_filename)

        assert mock_game_launcher_config.get_client_filename(
            input_client_type)[1] == expected_output_client_type
