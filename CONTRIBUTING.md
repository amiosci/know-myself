# KMS Contribution Guide

**TBD**

For the time being, PRs are welcome with no formal process for supporting merge.

#### Helpful commands

Assorted useful commands identified during development.

##### Remove unused requirements.txt dependencies

```shell
$ deptry . --ignore DEP001 --json-output deptry_findings.json;
$ cat deptry_findings.json | jq '.[].module' | xargs -I @ sed -i '/^@/d' requirements.txt;
```

Note: `deptry` seemingly has issues detecting transient dependencies provided from various `langchain` classes - such as document retrievers. Due to this, it is imperitive that all CUJ are exercised after applying this workflow. No current E2E tests exist which can accomplish this requirement.
