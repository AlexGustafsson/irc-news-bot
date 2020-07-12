FROM python:3-buster

RUN addgroup --gid 6697 irc-bot && \
    adduser --uid 6697 --ingroup irc-bot --no-create-home --quiet --disabled-password --gecos "" irc-bot

WORKDIR /etc/irc-bot
COPY Makefile requirements.txt ./
RUN make install-virtual-environment install-dependencies

USER irc-bot
COPY . .

ENV PATH /etc/irc-bot/venv/bin

ENTRYPOINT ["python3", "-m", "bot.main"]
