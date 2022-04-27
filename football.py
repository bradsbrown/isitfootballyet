import dataclasses
import datetime
import enum
import functools
import pathlib
import re
import time
import typing
import zoneinfo

import dash
import feedparser
import requests
from flask.helpers import send_from_directory

SAMPLE = {
    "title": "9/4 6:00 PM [W] Baylor University Football at Texas State",
    "title_detail": {
        "type": "text/plain",
        "language": None,
        "base": "",
        "value": "9/4 6:00 PM [W] Baylor University Football at Texas State",
    },
    "summary": "[W] Baylor University Football at Texas State\\nW 29-20\\nTV: ESPN+\\nStreaming Video: https://www.espn.com/watch/player?id=31d4ca58-78b7-47be-9889-cb3dca129898\\nStreaming Audio: http://baylorbears.com/showcase?Live=1593\\n https://baylorbears.com/calendar.aspx?id=26078",
    "summary_detail": {
        "type": "text/html",
        "language": None,
        "base": "",
        "value": "[W] Baylor University Football at Texas State\\nW 29-20\\nTV: ESPN+\\nStreaming Video: https://www.espn.com/watch/player?id=31d4ca58-78b7-47be-9889-cb3dca129898\\nStreaming Audio: http://baylorbears.com/showcase?Live=1593\\n https://baylorbears.com/calendar.aspx?id=26078",
    },
    "links": [
        {
            "rel": "alternate",
            "type": "text/html",
            "href": "https://baylorbears.com/calendar.aspx?id=26078",
        }
    ],
    "link": "https://baylorbears.com/calendar.aspx?id=26078",
    "id": "https://baylorbears.com/calendar.aspx?id=26078",
    "guidislink": False,
    "ev_location": "San Marcos, TX",
    "ev_startdate": "2021-09-04T23:00:00.0000000Z",
    "ev_enddate": "2021-09-05T02:00:00.0000000Z",
    "s_localstartdate": "2021-09-04T18:00:00.0000000",
    "s_localenddate": "2021-09-04T21:00:00.0000000",
    "s_teamlogo": "https://baylorbears.com/images/logos/site/site.png",
    "s_opponentlogo": "https://baylorbears.com/images/logos/texas_state_200x200.png",
    "s_opponent": "Texas State",
    "s_gameid": "26078",
    "s_gamepromoname": "",
    "s_links": "",
}


#########################
# Configurable Settings #
#########################
CALENDAR_URL = "https://baylorbears.com/calendar.ashx/calendar.rss"
SPORT_ID = 4
HOME_LOCATION = "Waco"

HEADERS = {"user-agent": "IsItFootballYet/2.6.0"}
DATE_RE = re.compile(r"\d{4}\-\d{1,2}\-\d{1,2}")
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
HTML_RE = re.compile(r"http(s)?://(\S)+")

#################
# School Colors #
#################


class SchoolColors(enum.Enum):
    GREEN = "#154734"
    GOLD = "#FFB81C"
    WHITE = "#FFFFFF"
    GREY = "#707372"


#######################
# Data Collection Code#
#######################


@dataclasses.dataclass
class ScheduleEntry:
    start_time: typing.Union[datetime.datetime, str]
    opponent: str
    summary: str
    team_logo: str
    opponent_logo: str
    streaming_links: typing.Dict[str, str]
    calendar_link: str
    location: str
    team: str = "Baylor University"

    @property
    def is_home(self):
        return self.location.startswith(HOME_LOCATION)

    @property
    def title(self):
        splitter = "vs." if self.is_home else "at"
        return f"{self.team} {splitter} {self.opponent}"

    @property
    def host(self):
        return self.team if self.is_home else self.opponent

    @property
    def host_logo(self):
        return self.team_logo if self.is_home else self.opponent_logo

    @property
    def guest(self):
        return self.opponent if self.is_home else self.team

    @property
    def guest_logo(self):
        return self.opponent_logo if self.is_home else self.team_logo

    @property
    def local_date(self):
        desc = self.start_time
        if isinstance(desc, datetime.datetime):
            desc = desc.strftime("%A, %b %d, %Y")
        return desc

    @property
    def local_time(self):
        desc = self.start_time
        if isinstance(desc, datetime.datetime):
            if desc.time() == datetime.time(0, 0):
                desc = "TBA"
            else:
                desc = desc.strftime("%I:%M %p")
        return desc


def _build_entry(entry):
    start_time = entry["ev_startdate"]
    if DATE_RE.match(start_time):
        date = datetime.date.fromisoformat(start_time)
        start_time = datetime.datetime(
            date.year, date.month, date.day, tzinfo=datetime.timezone.utc
        )
    else:
        try:
            time_str = f"{start_time.split('.')[0]}+0000"
            start_time = datetime.datetime.strptime(time_str, DATE_FORMAT)
            start_time = start_time.astimezone(zoneinfo.ZoneInfo("America/Chicago"))
        except:
            pass
    summary_lines = entry["summary"].split("\\n")
    streaming_links = {
        k.rstrip(":"): v
        for k, v in [l.rsplit(" ", 1) for l in summary_lines]
        if HTML_RE.match(v)
    }
    return ScheduleEntry(
        start_time=start_time,
        opponent=entry["s_opponent"],
        summary=entry["summary"],
        team_logo=entry["s_teamlogo"],
        opponent_logo=entry["s_opponentlogo"],
        calendar_link=entry["link"],
        streaming_links=streaming_links,
        location=entry["ev_location"],
    )


def _get_calendar(year=None):
    params = {"sport_id": SPORT_ID}
    res = requests.get(CALENDAR_URL, params=params, headers=HEADERS)
    res.raise_for_status()
    data = feedparser.parse(res.text)
    res = [_build_entry(d) for d in data["entries"]]
    return res


@functools.lru_cache
def get_calendar(ttl_hash):
    return _get_calendar()


def get_ttl_hash(seconds=3600):
    return round(time.time() / seconds)


def _is_football(events):
    current = datetime.date.today()
    return events[0].start_time.date() <= current <= events[-1].start_time.date()


############
# API Code #
############


app = dash.Dash(__name__, title="Is It Football Yet?")
app.css.config.serve_locally = True
server = app.server


@app.server.route("/assets/<path:path>")
def static_file(path):
    static_folder = pathlib.Path.cwd() / "assets"
    return send_from_directory(static_folder, path)


def school_logo(name, logo, home=True):
    color = SchoolColors.GOLD if home else SchoolColors.GREY
    name_style = {
        "color": color.value,
        "verticalAlign": "middle",
        "textAlign": "center",
    }
    img_style = {"maxWidth": "150px"}
    return [
        dash.html.Div(name, style=name_style),
        dash.html.Img(src=logo, style=img_style),
    ]


def events_by(include_past=False):
    events = get_calendar(get_ttl_hash())
    if not include_past:
        events = [e for e in events if e.start_time.date() >= datetime.date.today()]
    return events


def _first_saturday(year):
    month_start = datetime.date(year, 9, 1)
    day = month_start
    while day.weekday() != 5:
        day = day + datetime.timedelta(days=1)
    return day


def get_estimate_start_date():
    today = datetime.date.today()
    current_year = today.year

    this_year_sat = _first_saturday(current_year)
    date = this_year_sat if this_year_sat > today else _first_saturday(current_year + 1)

    return datetime.datetime(
        date.year,
        date.month,
        date.day,
        11,
        tzinfo=zoneinfo.ZoneInfo("America/Chicago"),
    )


class UnitsInSeconds(enum.Enum):
    second = 1
    minute = 1 * 60
    hour = 1 * 60 * 60


@dataclasses.dataclass()
class TimeBreakdown:
    seconds: int
    minutes: int
    hours: int
    days: int
    weeks: int

    @property
    def countdown_values(self):
        values = [
            ("Weeks", self.weeks),
            ("Days", self.days),
            ("Hours", self.hours),
            ("Minutes", self.minutes),
            ("Seconds", self.seconds),
        ]
        start = next((index for index, value in enumerate(values) if value[1] != 0))
        return values[start:]

    @staticmethod
    def from_timedelta(td):
        weeks = 0
        days = td.days
        if days > 7:
            weeks = days // 7
            days = td.days - (weeks * 7)

        hours = 0
        minutes = 0
        seconds = td.seconds
        if seconds > UnitsInSeconds.hour.value:
            hours = seconds // UnitsInSeconds.hour.value
            seconds = seconds - (hours * UnitsInSeconds.hour.value)
        if seconds > UnitsInSeconds.minute.value:
            minutes = seconds // UnitsInSeconds.minute.value
            seconds = seconds - minutes * UnitsInSeconds.minute.value

        return TimeBreakdown(
            weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds
        )


def _get_rows(include_past=False):
    events = events_by(include_past=include_past)
    if events:
        return [
            dash.html.H3(
                "Upcoming Games",
                style={"textAlign": "center", "color": SchoolColors.GOLD.value},
            ),
            dash.html.Table(
                dash.html.Tbody(
                    [
                        dash.html.Tr(
                            [
                                dash.html.Td(
                                    school_logo(event.team, event.team_logo),
                                ),
                                dash.html.Td(
                                    [
                                        dash.html.Div(
                                            dash.html.A(
                                                event.title, href=event.calendar_link
                                            )
                                        ),
                                        dash.html.Div(event.location),
                                    ],
                                    style={"color": SchoolColors.WHITE.value},
                                ),
                                dash.html.Td(
                                    [
                                        dash.html.Div(event.local_date),
                                        dash.html.Div(event.local_time),
                                    ],
                                    style={"color": SchoolColors.WHITE.value},
                                ),
                                dash.html.Td(
                                    [
                                        dash.html.A(k, href=v)
                                        for k, v in event.streaming_links.items()
                                    ]
                                ),
                                dash.html.Td(
                                    school_logo(
                                        event.opponent, event.opponent_logo, home=False
                                    )
                                ),
                            ]
                        )
                        for event in events
                    ]
                ),
                style={"marginLeft": "auto", "marginRight": "auto", "width": "90%"},
            ),
        ]


def football_answer():
    common_style = {"textAlign": "center", "fontSize": "80px"}
    if _is_football(get_calendar(get_ttl_hash())):
        return dash.html.H1(
            "YES",
            style={"color": SchoolColors.GOLD.value, **common_style},
        )
    return dash.html.H1("NO", style={"color": SchoolColors.GREY.value, **common_style})


app.layout = dash.html.Div(
    [
        dash.html.Div(football_answer()),
        dash.html.Div(id="countdown", style={"margin": "auto", "width": "25%"}),
        dash.html.Div(_get_rows(), id="table"),
        dash.dcc.Interval(id="interval"),
        dash.html.Link(rel="stylesheet", href="/assets/style.css"),
    ],
    style={
        "backgroundColor": SchoolColors.GREEN.value,
        "marginTop": "0px",
        "marginBottom": "0px",
        "padding": "0px",
    },
)


@app.callback(
    dash.dependencies.Output("countdown", "children"),
    [dash.dependencies.Input("interval", "n_intervals")],
)
def update_countdown(n):
    upcoming = events_by(include_past=False)
    if upcoming:
        next_event = upcoming[0].start_time
        title = "Next Game"
    else:
        next_event = get_estimate_start_date()
        title = "Next Season Start (est)"
    difference = TimeBreakdown.from_timedelta(
        next_event - datetime.datetime.now(tz=zoneinfo.ZoneInfo("America/Chicago"))
    )
    difference_divs = [
        dash.html.Div(
            f"{label}: {count}",
            style={
                "color": SchoolColors.GOLD.value,
                "textAlign": "center",
                "fontSize": "50px",
            },
        )
        for (label, count) in difference.countdown_values
    ]
    return [
        dash.html.H2(
            title,
            style={
                "color": SchoolColors.GOLD.value,
                "textAlign": "center",
                "fontSize": "60px",
            },
        ),
        *difference_divs,
    ]


if __name__ == "__main__":
    app.run_server(debug=True, port=6158)
