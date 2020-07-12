
import datetime
import jinja2
import os
import pathlib
import pprint
import re
import sys

from python_graphql_client import GraphqlClient

ORG_QUERY="""
query {
  viewer {
    organizations(first: 100, after:%s) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        login
        name
        description
        url
      }
    }
  }
}
"""

def make_query(query, after_cursor=None):
    """ Insert the cursor into the query """
    
    return query % (after_cursor or "null")

def org_parser(result, data):
    """ Parse the requested data """

    pprint.pprint(data)

    orgs = {}

    for org in data:
        orgs[org["login"]] = org

    result.setdefault("orgs", {})
    result["orgs"].update(orgs)

def fetch_ql(client, oauth_token, query, category, parser):
    has_next_page = True
    after_cursor = None

    result = {}

    while has_next_page:
        data = client.execute(
            query=make_query(query, after_cursor),
            headers={"Authorization": "Bearer {}".format(oauth_token)},
        )

        pprint.pprint(data)

        viewer = data["data"]["viewer"]
        parser(result, viewer[category]["nodes"])
        has_next_page = viewer[category]["pageInfo"][
            "hasNextPage"
        ]
        after_cursor = viewer[category]["pageInfo"]["endCursor"]

    return result

def main():

    root = pathlib.Path(__file__).parent.parent.resolve()
    print("root: %s" % root)
    client = GraphqlClient(endpoint="https://api.github.com/graphql")

    token = os.environ.get("JCHONIG_TOKEN", "")

    template = "README.md.j2"

    params = {
        'created': {
            'template': "README.md.j2",
            'at': datetime.datetime.utcnow().isoformat()
        }
    }

    params.update(fetch_ql(client, token, ORG_QUERY, "organizations", org_parser))

    pprint.pprint(params)

    j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(
        os.path.join(root, "templates"),
        followlinks=True))

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
