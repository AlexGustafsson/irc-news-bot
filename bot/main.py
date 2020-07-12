"""Main bot entrypoint."""

import logging
from argparse import ArgumentParser

from pygooglenews import GoogleNews

from irc import IRC
from irc.messages import IRCMessage

logger = logging.getLogger(__name__)


def handle_topic(irc: IRC, google_news: GoogleNews, target: str, topic: str) -> None:
    """Handle a topic request."""
    irc.send_message(target, "Working on it")
    logger.info("Fetching news for topic %s", topic)
    try:
        news = google_news.topic_headlines(topic)
        for entry in news["entries"][:5]:
            irc.send_message(target, entry["title"])
    except Exception as exception:  # pylint: disable=broad-except
        if str(exception) == "unsupported topic":
            # See: https://github.com/kotartemiy/pygooglenews#stories-by-topic-1
            irc.send_message(target, "That topic is not supported. Supported topics are:")
            irc.send_message(target, "world, nation, business, technology, entertainment, science, sports, health")
        else:
            raise exception


def handle_location(irc: IRC, google_news: GoogleNews, target: str, location: str) -> None:
    """Handle a location request."""
    irc.send_message(target, "Working on it")
    logger.info("Fetching news for location %s", location)
    news = google_news.geo_headlines(location)
    for entry in news["entries"][:5]:
        irc.send_message(target, entry["title"])


def handle_search(irc: IRC, google_news: GoogleNews, target: str, query: str) -> None:
    """Handle a search request."""
    irc.send_message(target, "Working on it")
    logger.info("Fetching news for query %s", query)
    news = google_news.search(query)
    for entry in news["entries"][:5]:
        irc.send_message(target, entry["title"])


def handle_top(irc: IRC, google_news: GoogleNews, target: str) -> None:
    """Handle a search request."""
    irc.send_message(target, "Working on it")
    logger.info("Fetching top news")
    news = google_news.top_news()
    for entry in news["entries"][:5]:
        irc.send_message(target, entry["title"])


def handle_news_request(irc: IRC, nick: str, target: str, message: IRCMessage) -> None:
    """Handle a news request."""
    words = message.message.replace("{}:".format(nick), "").strip().split()
    if len(words) < 3:
        irc.send_message(target, "Bad command. See help message")
        return
    command = words[0]
    country = words[1]
    language = words[2]
    parameter = " ".join(words[3:])

    logger.info("Handling news request. Command=%s, country=%s, language=%s", command, country, language)
    google_news = GoogleNews(country=country, lang=language)

    try:
        if command == "topic":
            handle_topic(irc, google_news, target, parameter)
        elif command == "location":
            handle_location(irc, google_news, target, parameter)
        elif command == "search":
            handle_search(irc, google_news, target, parameter)
        elif command == "top":
            handle_top(irc, google_news, target)
        else:
            irc.send_message(target, "I don't recognize that command")
    except Exception:  # pylint: disable=broad-except
        logger.error("Unable to fetch news", exc_info=True)
        irc.send_message(target, "I was unable to fetch news")


def main() -> None:
    """Main entrypoint of the bot."""
    # Configure the default logging format
    logging.basicConfig(
        format="[%(asctime)s] [%(name)s] [%(levelname)-5s] %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create an argument parser for parsing CLI arguments
    parser = ArgumentParser(description="An IRC bot for reading news")

    # Add parameters for the server connection
    parser.add_argument("-s", "--server", required=True, type=str, help="The server to connect to")
    # Add optional parameters for the server connection
    parser.add_argument("-p", "--port", default=6697, type=int, help="The port to connect to")
    parser.add_argument("--use-tls", default=True, type=bool, help="Whether or not to use TLS")
    parser.add_argument("-t", "--timeout", default=300, type=float, help="Connection timeout in seconds")

    # Add optional parameters for authentication etc.
    parser.add_argument("-u", "--user", default="news-bot", help="Username to use when connecting to the IRC server")
    parser.add_argument("-n", "--nick", default="news-bot", help="Nick to use when connecting to the IRC server")
    parser.add_argument(
        "-g",
        "--gecos",
        default="News Bot v0.1.0 (github.com/AlexGustafsson/irc-news-bot)",
        help="Gecos to use when connecting to the IRC server"
    )
    parser.add_argument(
        "-c",
        "--channel",
        required=True,
        action="append",
        help="Channel to join. May be used more than once"
    )

    # Parse the arguments
    options = parser.parse_args()

    # Create an IRC connection
    irc = IRC(
        options.server,
        options.port,
        options.user,
        options.nick,
        timeout=options.timeout,
        use_tls=options.use_tls
    )

    irc.connect()

    # Connect to specified channels
    for channel in options.channel:
        irc.join(channel)

    # Handle all messages
    for message in irc.messages:
        if not isinstance(message, IRCMessage):
            continue

        target = message.author if message.target == options.nick else message.target

        if message.message == "{}: help".format(options.nick):
            irc.send_message(target, "I help you read news.")
            irc.send_message(target, "You can use the following commands:")
            irc.send_message(
                target,
                "{}: topic se sv business -> Swedish business news on Swedish".format(options.nick)
            )
            irc.send_message(
                target,
                "{}: location se sv Karlskrona -> Swedish news on Swedish from Karlskrona".format(options.nick)
            )
            irc.send_message(
                target,
                "{}: search us en security -TikTok -> American news in English about security, not mentioning TikTok"
                .format(options.nick)
            )
            irc.send_message(target, "{}: help -> this help text".format(options.nick))
        elif message.message.startswith("{}:".format(options.nick)):
            handle_news_request(irc, options.nick, target, message)


if __name__ == "__main__":
    main()
