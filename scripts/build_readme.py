
import datetime
import jinja2
import os
import pathlib
import pprint
import re
import sys

from python_graphql_client import GraphqlClient

REPO_QUERY="""
query {
  viewer {
    repositories(first: 100, privacy:PUBLIC, after:%s) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        name
	nameWithOwner
        description
        isArchived
        isFork
        parent {
          nameWithOwner
          url
        }
        stargazers {
          totalCount
        }
        url
      }
    }
  }
}
"""

ORG_QUERY="""
query {
  viewer {
    organizations(first: 100, after:%s) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        avatarUrl(size: 40)
        login
        name
        description
        url
      }
    }
  }
}
"""

def repo_parser(result, data):
    """ Parse the repo data """

    repos = {}

    for repo in data:
        if repo["nameWithOwner"].startswith("FRC5254"):
            continue
        repos[repo["nameWithOwner"]] = repo

    result.setdefault("repos", {})
    result["repos"].update(repos)

def make_query(query, after_cursor=None):
    """ Insert the cursor into the query """
    
    return query % (after_cursor or "null")

def org_parser(result, data):
    """ Parse the requested data """

    orgs = {}

    for org in data:
        orgs[org["login"]] = org

    result.setdefault("orgs", {})
    result["orgs"].update(orgs)

def fetch_ql(client, oauth_token, query, category, parser):
    """ Execute a query and return the data """
    has_next_page = True
    after_cursor = None

    result = {}

    while has_next_page:
        data = client.execute(
            query=make_query(query, after_cursor),
            headers={"Authorization": "Bearer {}".format(oauth_token)},
        )

        viewer = data["data"]["viewer"]
        parser(result, viewer[category]["nodes"])
        has_next_page = viewer[category]["pageInfo"][
            "hasNextPage"
        ]
        after_cursor = viewer[category]["pageInfo"]["endCursor"]

    return result

def main():
    """ Where it all happens """

    root = pathlib.Path(__file__).parent.parent.resolve()
    print("root: %s" % root)
    client = GraphqlClient(endpoint="https://api.github.com/graphql")

    token = os.environ.get("JCHONIG_TOKEN", "")

    # Set up our environment to find the template
    j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(
        os.path.join(root, "templates"),
        followlinks=True))
    template = "README.md.j2"

    params = {
        'created': {
            'template': "README.md.j2",
            'at': datetime.datetime.utcnow().isoformat()
        }
    }

    params.update(fetch_ql(client, token, ORG_QUERY, "organizations", org_parser))
    params.update(fetch_ql(client, token, REPO_QUERY, "repositories", repo_parser))

    pprint.pprint(params)

    try:
        contents = j2_env.get_template(template).render(**params)
    except jinja2.exceptions.TemplateNotFound as error:
        print("Template not found: %s" % error)
        return
    except (TypeError, jinja2.exceptions.TemplateError) as error:
        print("Templating error: %s" % error)
        return

    with open(os.path.join(root, "README.md"), "w") as filep:
        filep.write(contents)
        
if __name__ == "__main__":
    main()
    sys.exit(0)
