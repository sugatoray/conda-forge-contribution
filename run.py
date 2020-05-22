import sys
import getopt
import requests
from jinja2 import Template


query_template = """
{
  organization(login: "conda-forge") {
{%- if after %}
    teams(first: 100, after: "{{ after }}", userLogins: ["{{ githubuser }}"]) {
{%- else %}
    teams(first: 100, userLogins: ["{{ githubuser }}"]) {
{%- endif %}
      totalCount
      edges {
        node {
          name
          description
        }
      }
      pageInfo {
        endCursor
        hasNextPage
      }
    }
  }
}
"""


def get_all_package_names(username, token):
    t = Template(query_template)
    after = None 
    next_page = True 
    packages_lst = []
    while next_page: 
        query = t.render(githubuser=username, after=after)
        request = requests.post('https://api.github.com/graphql', json={'query': query}, headers={"Authorization": token})
        if request.status_code == 200:
            result_dict = request.json()
        else:
            raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
        next_page = result_dict['data']['organization']['teams']['pageInfo']['hasNextPage']
        after = result_dict['data']['organization']['teams']['pageInfo']['endCursor']
        for n in result_dict['data']['organization']['teams']['edges']:
            if n['node']['name'] not in ['all-members', 'Core']:
                packages_lst.append(n['node']['name'])
    return packages_lst


def read_template(file):
    with open(file, 'r') as f:
        return f.read()


def write_index(file, output):
    with open(file, 'w') as f: 
        f.writelines(output)


def command_line(argv):
    username = None
    token = None
    try:
        opts, args = getopt.getopt(
            argv, "u:t:h", ["username=", "token=", "help"]
        )
    except getopt.GetoptError:
        print("run.py -u <username> -t <token>")
        sys.exit()
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("run.py -u <username> -t <token>")
            sys.exit()
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-t", "--token"):
            token = arg
    total_packages = get_all_package_names(username=username, token="bearer "+token)
    web = Template(read_template(file="template.html"))
    web_output = web.render(package_lst=total_packages)
    write_index(file="index.html", output=web_output)
    md = Template(read_template(file="template.md"))
    md_output = md.render(package_lst=total_packages)
    write_index(file="packages.md", output=md_output)


if __name__ == "__main__":
    command_line(sys.argv[1:])
