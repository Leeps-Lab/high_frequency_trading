import requests
import csv
import os


def headers(token):
    headers = {
        'authorization': token,
        'Accept': 'application/vnd.github.v4.raw'
        }
    return headers


def get(url, headers):
    response = requests.get(url, headers=headers)
    data = response.content.decode('utf-8')
    out = data.split()
    return out


def extract_name(url):
    csv_name = url.split('/')[-1]
    return csv_name


def write(data, directory, filename):
    path = os.path.join(directory, filename)
    with open(path, 'w') as f:
        writer = csv.writer(f, delimiter=',')
        for row in data:
            splitted = row.split(',')
            writer.writerow(splitted)


def main(token, url, direc):
    h = headers(token)
    data = get(url, h)
    filename = extract_name(url)
    write(data, direc, filename)

if __name__ == '__main__':
    pass
