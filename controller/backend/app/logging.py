import logging


def register_log_filter() -> None:
    """
    Removes logs from healthiness/readiness endpoints so they don't spam
    and pollute application log flow
    """

    class EndpointFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return (
                record.args  # type: ignore
                and len(record.args) >= 3
                and "/netify" not in record.args[2]  # type: ignore
            )

    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
