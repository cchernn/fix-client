import os
import quickfix
import datetime
from application import fix_pricing
from helpers import log, saveData, ensureDirectories
from report import processData

def main():
    now = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
    ensureDirectories()
    config_file = "config.cfg"
    data_filepath = f"Results/market_data_{now}.csv"

    try:
        fix_session = fix_pricing(quickfix.Session, start_timestamp=now)
        fix_settings = quickfix.SessionSettings(config_file)
        store_factory = quickfix.FileStoreFactory(fix_settings)
        log_factory = quickfix.ScreenLogFactory(fix_settings)

        initiator = quickfix.SocketInitiator(
            fix_session,
            store_factory,
            fix_settings,
            log_factory,
        )

        initiator.start()
        fix_session.run()
    except (quickfix.ConfigError, quickfix.RuntimeError, KeyboardInterrupt) as ex:
        log(fix_session.logger, ex, level="ERROR", _print=True)
    finally:
        saveData(data=fix_session._Market_Data, filepath=data_filepath)
        initiator.stop()
        if os.path.exists(data_filepath):
            processData(filepath=data_filepath, sessionid=fix_session.sessionID, start_timestamp=now)

if __name__ == "__main__":
    main()
