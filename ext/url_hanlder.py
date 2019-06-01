import re
from urllib.parse import quote

__SCHEME_TO_PORT__ = {
    'ftp': '21',
    'ssh': '22',
    'telnet': '23',
    'tftp': '69',
    'socks4': '1080',
    'socks5': '1080',
    'http': '80',
    'pop2': '109',
    'pop3': '110',
    'sftp': '115',
    'https': '443',
    'sqlserver': '1433',
    'mysql': '3306',
    'postgresql': '5432',
    'redis': '6379',
}


class DictString(dict):
    def __setitem__(self, key, value):
        super().__setitem__(key, str(value))


class Url:
    def __init__(self, url: str):
        '''
        :param url: 需要解析的url
        https://example.com:8952/nothing.py;param1=v1;param2=v2?query1=v1&query2=v2#frag
        scheme=>https, netloc=>example.com:8952, path=>/nothing.py, params=>param1=v1;param2=v2,
        query=>query1=v1&query2=v2, fragment=>frag, hostname=>example.com, port=>8952
        '''
        self.scheme, self.netloc, self.path, self.params, self.query = '', '', '', DictString(), DictString()
        self.fragment, self.hostname, self.port, self.username, self.password = '', '', '', '', ''

        try:
            self.scheme, user_pass, self.netloc, self.path = re.search(
                r'(.+)://([^\\//]*:[^\\//]*@)?([^\\//]+)(/[^;?#]*)?', url).groups()
            if not self.path:
                self.path = '/'
            if user_pass:
                self.username, self.password = re.search(r'([^@:]+):([^@:]+)', user_pass).groups()

            self.hostname, self.port = re.search(r'([^:]+):?(\d+)?', self.netloc).groups()
            if not self.port:
                self.port = self.get_default_port(self.scheme)
        except AttributeError:
            raise ValueError('Incorrect URL')

        r = re.findall(r';([^?#]+?)=([^?#;]+)', url)
        if r:
            self.params = DictString(r)
        else:
            self.params = DictString()

        r = re.findall(r'[?&]([^;?#]+?)=([^;?#&]+)', url)
        if r:
            self.query = DictString(r)
        else:
            self.query = DictString()

        r = re.search(r'#([^;?#]+)', url)
        if r:
            self.fragment = r.group(1)

    @classmethod
    def get_default_port(cls, scheme):
        return __SCHEME_TO_PORT__[scheme]

    def url_index(self):
        base = f'{self.scheme}://'
        if self.username:
            base += f'{self.username}:{self.password}@'
        base += self.netloc
        return base

    def path_full(self, encoded=True):
        base = self.path
        if self.params:
            base += self.params_string(True, encoded)
        if self.query:
            base += self.query_string(True, encoded)
        if self.fragment:
            base += f'#{self.fragment}'
        return base

    def url_full(self, encoded=True):
        return self.url_index() + self.path_full(encoded)

    def query_string(self, flag: bool = False, encoded: bool = True):
        base = ''
        if self.query:
            first = True
            for k in self.query:
                if first:
                    if flag:
                        base += '?'
                    first = False
                else:
                    base += f'&'
                base += f'{k}={quote(self.query[k]) if encoded else self.query[k]}'
        return base

    def params_string(self, flag: bool = False, encoded: bool = True):
        base = ''
        if self.params:
            first = True
            for k in self.params:
                if first:
                    if not flag:
                        base += f'{k}={quote(self.params[k]) if encoded else self.params[k]}'
                        continue
                    first = False
                base += f';{k}={quote(self.params[k]) if encoded else self.params[k]}'
        return base

    def __str__(self):
        return f"URL(scheme={self.scheme}, netloc={self.netloc}, path={self.path}, params={self.params}, query={self.query}, fragment={self.fragment}, hostname={self.hostname}, port={self.port}, username={self.username}, password={self.password})"


if __name__ == '__main__':
    u = Url('https://example.com:8952/nothing.py;param1=v1;param2=v2?query1=v1&query2=v2#frag')
    print(u.url_index())
    print(u.path_full())
    print(u.url_full())
    print(u.url_full(encoded=False))
    u = Url('https://example.com:8952/nothing.py?query1=val$@!{}wef e()<>&query2=你好吗#frag')
    print(u.url_index())
    print(u.path_full())
    print(u.url_full())
    print(u.url_full(encoded=False))
    u = Url('socks://login:p4ssw0rd@example.com:8952/nothing.py#frag')
    print(u.url_index())
    print(u.path_full())
    print(u.url_full())
    print(u.url_full(encoded=False))
    u = Url('https://example.com:8952/;param1=v1;param2=v2?query1=val$@!{}waf() <>&query2=你好吗')
    print(u.query_string())
    print(u.query_string(flag=True))
    print(u.query_string(encoded=False))

    print(u.params_string())
    print(u.params_string(flag=True))
