
import datetime
import jinja2
import json
import os
import pathlib
import re
import sys

from python_graphql_client import GraphqlClient

ORG_QUERY="""
query {
  viewer {
    organizations(first: 100, after:{after_cursor}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {n
        name
        descriptionHTML
        url
      }
    }
  }
}
"""

def make_query(query, after_cursor=None):
    """ Insert the cursor into the query """
    
    return query.format(after_cursor=after_cursor or "null")

def fetch_orgs(oauth_token):
    has_next_page = True
    after_cursor = None

    while has_next_page:
        data = client.execute(
            query=make_query(ORG_QUERY, after_cursor),
            headers={"Authorization": "Bearer {}".format(oauth_token)},
        )
        print()
        print(json.dumps(data, indent=4))
        print()
        for repo in data["data"]["viewer"]["repositories"]["nodes"]:
            if repo["releases"]["totalCount"] and repo["name"] not in repo_names:
                repos.append(repo)
                repo_names.add(repo["name"])
                releases.append(
                    {
                        "repo": repo["name"],
                        "release": repo["releases"]["nodes"][0]["name"]
                        .replace(repo["name"], "")
                        .strip(),
                        "published_at": repo["releases"]["nodes"][0][
                            "publishedAt"
                        ].split("T")[0],
                        "url": repo["releases"]["nodes"][0]["url"],
                    }
                )
        has_next_page = data["data"]["viewer"]["repositories"]["pageInfo"][
            "hasNextPage"
        ]
        after_cursor = data["data"]["viewer"]["repositories"]["pageInfo"]["endCursor"]
    return releases


def main():

    root = pathlib.Path(__file__).parent.parent.resolve()
    print("root: %s" % root)
    client = GraphqlClient(endpoint="https://api.github.com/graphql")

    token = os.environ.get("JCHONIG_TOKEN", "")

    template = "README.md.j2"

    params = { }
    params['created']['template'] = "README.md.j2"
    params['created']['at'] = datetime.datetime.utcnow().isoformat()

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
