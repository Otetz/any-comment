import random
import statistics
import time
from typing import Iterator, Callable, List, Tuple

import requests
from colorama import Fore, Style, init

ITERATIONS = 10
THRESHOLD_FIRST = 1000
FORMATS = [None, 'json', 'csv', 'xml']

# SELECT commentid FROM comments WHERE parentid < (SELECT min(entityid) FROM comments)
comments = [320283, 320284, 320285, 320286, 320287, 320288, 320289, 320290, 320291, 320292, 320293, 320294, 320295,
            320296, 320297, 320298, 320299, 320300, 320301, 320302, 320303, 320304, 320305, 320306, 320307, 320308,
            320309, 320310, 320311, 320312, 320313, 320314, 320315, 320316, 320317, 320318, 320319, 320320, 320321,
            320322]
posts = [391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405,
         406, 407, 408, 409, 410, 411, 412, 413]
users = [316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330,
         331, 332, 333, 334, 335]


class StartOverException(Exception):
    pass


def comments_descendants(commentid: int, fmt: str) -> Iterator:
    r = requests.get('http://localhost:5000/api/1.0/comments/%d/descendants%s' % (commentid, fmt), stream=True)
    for line in r.iter_lines():
        if line:
            yield line.decode(fmt == '.csv' and 'windows-1251' or 'utf-8')


def posts_descendants(postid: int, fmt: str) -> Iterator:
    r = requests.get('http://localhost:5000/api/1.0/posts/%d/descendants%s' % (postid, fmt), stream=True)
    for line in r.iter_lines():
        if line:
            yield line.decode(fmt == '.csv' and 'windows-1251' or 'utf-8')


def users_descendants(userid: int, fmt: str) -> Iterator:
    r = requests.get('http://localhost:5000/api/1.0/users/%d/descendants%s' % (userid, fmt), stream=True)
    for line in r.iter_lines():
        if line:
            yield line.decode(fmt == '.csv' and 'windows-1251' or 'utf-8')


def users_comments(userid: int, fmt: str) -> Iterator:
    r = requests.get('http://localhost:5000/api/1.0/users/%d/comments%s' % (userid, fmt), stream=True)
    for line in r.iter_lines():
        if line:
            yield line.decode(fmt == '.csv' and 'windows-1251' or 'utf-8')


def measure(func: Callable, ids: List[int], fmt: str) -> Tuple[List[float], List[float], List[int]]:
    arr_first = []
    arr_total = []
    arr_counts = []
    for _ in range(ITERATIONS):
        first_response = 180000
        attempts = 0
        while True:
            first = False
            try:
                i = 0
                rec_id = random.choice(ids)
                start = time.clock()
                # noinspection PyAssignmentToLoopOrWithParameter
                for _ in func(rec_id, fmt):
                    if not first:
                        first_response = time.clock()
                        first = True
                    i += 1
                total = time.clock()
                if i < 1000:
                    raise StartOverException()
                break
            except StartOverException:
                attempts += 1
                if attempts > len(ids) * 3:
                    return arr_first, arr_total, arr_counts
        to_first_response = (first_response - start) * 1000.0
        to_total = (total - start) * 1000.0
        arr_first.append(to_first_response)
        arr_total.append(to_total)
        arr_counts.append(i)
    return arr_first, arr_total, arr_counts


def perf_test(func: Callable, title: str, ids: List[int]) -> None:
    print(Fore.YELLOW + title + Style.RESET_ALL + ':')
    for fmt in FORMATS:
        format_title = Fore.CYAN + '[wo]'
        req_format = ''
        if fmt:
            format_title = Fore.CYAN + fmt.upper() + Style.RESET_ALL + ' attachment'
            req_format = '.' + fmt.lower()
        print('  ' + format_title + Style.RESET_ALL + ':')
        (arr_first, arr_total, arr_counts) = measure(func, ids, req_format)
        if not arr_counts:
            print('    ! ' + Fore.RED + 'skip' + Style.RESET_ALL + ' - no test data')
            continue
        first_response_mean = statistics.mean(arr_first)
        total_response_mean = statistics.mean(arr_total)
        first_color = Fore.GREEN
        if first_response_mean > THRESHOLD_FIRST:
            first_color = Fore.RED
        total_color = Fore.GREEN
        if total_response_mean > THRESHOLD_FIRST:
            total_color = Fore.YELLOW
        print('    first response: ' + first_color + ('%.3f ms ' % first_response_mean) +
              Style.RESET_ALL + 'average (stddev: %.3f)' % statistics.stdev(arr_first))
        print('    total response: ' + total_color + ('%.3f ms ' % total_response_mean) +
              Style.RESET_ALL + 'average (stddev: %.3f)' % statistics.stdev(arr_total))
        print('    -> over %d–%d items' % (min(arr_counts), max(arr_counts)))
    print()


if __name__ == '__main__':
    init(autoreset=True)

    # "Прогреваем" requests - зачастую первый запрос тормозит из-за первого использования
    requests.get('http://localhost:5000/')

    perf_test(comments_descendants, 'comments.descendants', comments)
    perf_test(posts_descendants, 'posts.descendants', posts)
    perf_test(users_descendants, 'users.descendants', users)
    perf_test(users_comments, 'users.comments', users)
