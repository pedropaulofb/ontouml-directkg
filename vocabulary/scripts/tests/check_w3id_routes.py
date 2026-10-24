"""Check the coordinated W3ID rules statically; this is not an HTTP test.

Usage: python vocabulary/scripts/tests/check_w3id_routes.py PATH/TO/.htaccess
       [--baseline PATH/TO/UPSTREAM/.htaccess]
Only the existing DirectKG RewriteEngine/RewriteCond/RewriteRule subset is read.
Apache parsing and eventual live HTTP checks remain separate validation steps.
"""
import argparse
import re
from pathlib import Path


SITE = 'https://pedropaulofb.github.io/ontouml-directkg'
REPO = 'https://github.com/pedropaulofb/ontouml-directkg'
ACCEPTS = ('', 'text/turtle', 'TEXT/TURTLE', 'text/html', '*/*',
           'application/ld+json', 'text/turtle;q=0', 'text/html;q=1,text/turtle;q=0.1')


def rules(path):
    result, condition = [], None
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip() or line.startswith('#') or line == 'RewriteEngine on':
            continue
        if line == 'RewriteCond %{HTTP_ACCEPT} text/turtle [NC]':
            assert condition is None
            condition = True
            continue
        parts = line.split()
        assert len(parts) == 4 and parts[0] == 'RewriteRule', (number, line)
        flags = re.fullmatch(r'\[R=(302|303),L\]', parts[3])
        assert flags, (number, line)
        result.append((number, re.compile(parts[1]), parts[2], int(flags[1]), condition))
        condition = None
    assert condition is None and len(result) == 14
    return result


def resolve(config, path, accept):
    for line, pattern, target, status, turtle in config:
        if turtle and 'text/turtle' not in accept.lower():
            continue
        match = pattern.search(path)
        if match:
            target = re.sub(r'\$(\d)', lambda m: match[int(m[1])] or '', target)
            return status, target, line, match.groups()
    return None


def check(candidate, baseline=None):
    config = rules(candidate)
    checks = 0
    witnesses = {}
    def expect(path, accept, expected):
        nonlocal checks
        observed = resolve(config, path, accept)
        assert (observed[:2] if observed else None) == expected, (path, accept, observed, expected)
        if observed:
            witnesses.setdefault(observed[2], (path, accept, observed[3]))
        checks += 1
    for version in (None, '0.1.0', '0.1.1', '0.0.0', '1.2.3', '10.20.30'):
        route = 'vocab/dkgm' + ('/' + version if version else '')
        ttl = f'{SITE}/vocabulary/versioned/dkgm-vocabulary-v{version}.ttl' if version else f'{SITE}/vocabulary/latest/dkgm-vocabulary.ttl'
        html = f'{SITE}/vocabulary/versioned/dkgm-vocabulary-v{version}.html' if version else f'{SITE}/vocabulary/latest/index.html'
        for suffix in ('', '/ttl', '/docs', '/spec'):
            for slash in ('', '/'):
                for accept in ACCEPTS:
                    target = ttl if suffix == '/ttl' or (not suffix and 'text/turtle' in accept.lower()) else html
                    expect(route + suffix + slash, accept, (302 if suffix else 303, target))
    project = {'': SITE + '/', 'docs': SITE + '/', 'git': REPO,
               'pypi': 'https://pypi.org/project/ontouml-directkg/',
               'releases/latest': REPO + '/releases/latest',
               'releases/v0.1.0': REPO + '/releases/tag/v0.1.0',
               'releases/v12.34.56': REPO + '/releases/tag/v12.34.56'}
    for route, target in project.items():
        for slash in (('', '/') if route else ('',)):
            for accept in ACCEPTS:
                expect(route + slash, accept, (302, target))
    retired = ['vocab' + version + suffix for version in ('', '/0.1.0', '/0.1.1')
               for suffix in ('', '/ttl', '/docs', '/spec')]
    invalid = ['vocab/dkgm' + suffix for suffix in ('//', '/X.Y.Z', '/01.2.3', '/1.02.3',
               '/1.2.03', '/1.2', '/1.2.3.4', '/v1.2.3', '/1.2.3-beta',
               '/1.2.3/other', '/other', 'Other', '/ttl/other')]
    invalid += ['vocabulary', 'releases/v01.2.3', 'releases/1.2.3', 'docs/other', 'git/other']
    for route in retired + invalid:
        for slash in ('', '/'):
            for accept in ACCEPTS:
                expect(route + slash, accept, None)
    assert len(witnesses) == 14, 'Every rule must have a matching witness'
    if baseline:
        original = rules(baseline)
        project_lines = lambda path: [s for s in path.read_text().splitlines()
                                      if s.startswith('RewriteRule ') and not s.startswith('RewriteRule ^vocab/')]
        assert project_lines(candidate) == project_lines(baseline), 'Unrelated project rules changed'
        for route in project:
            for accept in ACCEPTS:
                assert resolve(config, route, accept)[:2] == resolve(original, route, accept)[:2]
    for line, (path, accept, captures) in sorted(witnesses.items()):
        print(f'Rule line {line}: path={path!r}; Accept={accept!r}; captures={captures!r}')
    print(f'PASS: {checks} static route cases; all 14 rules exercised; no legacy routes or unintended matches.')
    if baseline:
        print('PASS: unrelated project rules are byte-identical and retain their modeled results.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('htaccess', type=Path)
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    check(args.htaccess, args.baseline)
