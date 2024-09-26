# 🦜️🔗 LangChain Unstructured

This repository contains 1 package with Unstructured integrations with LangChain:

- [langchain-unstructured](https://pypi.org/project/langchain-unstructured/)

## Initial Repo Checklist (Remove this section after completing)

This setup assumes that the partner package is already split. For those instructions,
see [these docs](https://python.langchain.com/docs/contributing/integrations#partner-packages).

In github (manual)

- [ ] Add integration testing secrets in Github (ask Erick for help)
- [ ] Add partner collaborators in Github (ask Erick for help)
- [ ] "Allow auto-merge" in General Settings 
- [ ] Only "Allow squash merging" in General Settings
- [ ] Set up ruleset matching CI build (ask Erick for help)
    - name: ci build
    - enforcement: active
    - bypass: write
    - target: default branch
    - rules: restrict deletions, require status checks ("CI Success"), block force pushes
- [ ] Set up ruleset
    - name: require prs
    - enforcement: active
    - bypass: none
    - target: default branch
    - rules: restrict deletions, require a pull request before merging (0 approvals, no boxes), block force pushes

Pypi (manual)

- [ ] Add new repo to test-pypi and pypi trusted publishing (ask Erick for help)

Slack

- [ ] Set up release alerting in Slack (ask Erick for help)

release:
/github subscribe langchain-ai/langchain-unstructured releases workflows:{name:"release"}
/github unsubscribe langchain-ai/langchain-unstructured issues pulls commits deployments
