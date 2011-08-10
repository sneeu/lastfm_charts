import datetime
import hashlib
import pickle
import sys

import svg


POINT_WIDTH = 4


def cumulative_versus(users):
    one_day = datetime.timedelta(days=1)
    first_day = datetime.date(2010, 12, 1)
    today = datetime.date.today()

    top_right = -1
    for __, data in users.items():
        top_right = max(top_right, sum(data.values()))

    width = (today - first_day).days * POINT_WIDTH
    height = 200

    scaler = float(top_right) / height
    scene = svg.Scene('versus', width=width, height=height)


    for i, (username, data) in enumerate(users.items()):
        colour = '#%s' % hashlib.md5(username).hexdigest()[:6]

        accumulator = 0

        day = first_day
        text_y = 20 + 24 * i
        text = '%s (%d)' % (username, sum(data.values()), )
        scene.add(svg.Text((10, text_y), text, 'fill:%s;stroke:none;font:16px Helvetica' % colour))

        while day < today + one_day:
            print accumulator

            day += one_day
            i = (day - first_day).days

            accumulator += data.get(day, 0)
            next_y = accumulator + data.get(day + one_day, 0)

            x1, y1 = i * POINT_WIDTH, float(accumulator) / scaler
            x2, y2 = x1 + POINT_WIDTH, float(next_y) / scaler

            print '  ', x1, x2

            scene.add(svg.Line((x1, height - y1), (x2, height - y2), style="stroke:%s" % colour))

    scene.write_svg()


def cumulative_versus_main(usernames):
    users = {}
    for username in usernames:
        data = pickle.load(open('%s.pickle' % username))
        users[username] = data
    cumulative_versus(users)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cumulative_versus_main(sys.argv[1:])
