# concourse-resource-bitbucket
[![Docker Pulls](https://img.shields.io/docker/pulls/karunamon/concourse-resource-bitbucket.svg?maxAge=2592000)](https://hub.docker.com/r/karunamon/concourse-resource-bitbucket/)
[![Requirements Status](https://requires.io/github/Karunamon/concourse-resource-bitbucket/requirements.svg?branch=master)](https://requires.io/github/Karunamon/concourse-resource-bitbucket/requirements/?branch=master)
[![Build Status](https://travis-ci.org/Karunamon/concourse-resource-bitbucket.svg?branch=master)](https://travis-ci.org/Karunamon/concourse-resource-bitbucket)

A [Concourse](http://concourse.ci/) [resource](http://concourse.ci/resources.html) to interact with the build status API of [Atlassian BitBucket](https://www.atlassian.com/software/bitbucket) instances, either the public instance at bitbucket.com, or a hosted instance on your own network.

This repo is tied to the [associated Docker image](https://hub.docker.com/r/karunamon/concourse-resource-bitbucket/) on Docker Hub, built from the master branch. The image is only rebuilt once the tests complete successfully, so you can be confident that the image you use on your Concourse has been tested and working successfully.

## Resource Configuration

These items go in the `source` fields of the resource type. Bold items are required:

 * **`bitbucket_user`** - Login username of someone with rights to the repository being updated.
 * **`bitbucket_password`** - Password for the mentioned user. For Bitbucket Cloud this will need to be an [app password](https://confluence.atlassian.com/bitbucket/app-passwords-828781300.html)
 * `debug` - When True, dump the JSON documents sent and received for troubleshooting. (default: false)
 * `driver` - Are you using Bitbucket Cloud or Bitbucket Server. (default: Bitbucket Server)
 * `repository_type` - The type of the repository, which can be either git or mercurial. (default: git)
 * `verify_ssl` - When False, ignore any HTTPS connection errors if generated. Useful if on an internal network. (default: True)

### `Bitbucket Cloud` Driver
* **`owner`** - The owner of the repository, which will either be a username or team
* **`repository_name`** - The name of the repository on Bitbucket Cloud

### `Bitbucket Server` Driver
* **`bitbucket_url`** - *base* URL of the bitbucket instance, including a trailing slash. (example: `https://bitbucket.mynetwork.com/`)
## Behavior


### `check`

No-op


### `in`

No-op

### `out`

Update the status of a commit.

Parameters:

 * **`repo`** - Name of the git repo containing the SHA to be updated. This will come from a previous `get` on a `git` resource. Make sure to use the git directory name, not the name of the resource.
 * **`build_status`** - the state of the status. Must be one of `SUCCESSFUL`, `FAILED`, or `INPROGRESS` - case sensitive.


## Example

A typical use case is to update the status of a commit as it traverses your pipeline. The following example marks the commit as pending before unit tests start. Once unit tests finish, the status is updated to either success or failure depending on how the task completes.

---
    resource_types:
      - name: bitbucket-notify
        type: docker-image
        source:
          repository: karunamon/concourse-resource-bitbucket

    resources:
      - name: testing-repo
        type: git
        source:
          uri: https://bitbucket.localnet/scm/~michael.parks/concourse-testing.git
          branch: master

      - name: bitbucket-notify
        type: bitbucket-notify
        source:
          bitbucket_url: https://bitbucket.localnet/
          bitbucket_username: bbuser
          bitbucket_password: bbpass
          verify_ssl: false


    jobs:
      - name: integration-tests
        plan:
        - get: testing-repo
          trigger: true

        - put: bitbucket-notify
          params:
            build_status: INPROGRESS
            repo: testing-repo

        - task: tests
          file: testing-repo/task.yml
          on_success:
            put: bitbucket-notify
            params:
              build_status: SUCCESSFUL
              repo: testing-repo
          on_failure:
            put: bitbucket-notify
            params:
              build_status: FAILED
              repo: testing-repo

In this example, notice that the repo: parameter is set to the same name as the testing-repo resource. To reiterate: **In your deployment, set the repo: field to the folder name of the git repo**, or in other words, what you'd end up with if you ran a `git clone` against the git URI.

## Installation

This resource is not included with the standard Concourse release. Use one of the following methods to make this resource available to your pipelines.


### Deployment-wide

To install on all Concourse workers, update your deployment manifest properties to include a new `groundcrew.resource_types` entry...

    properties:
      groundcrew:
        additional_resource_types:
          - image: "docker:///karunamon/concourse-resource-bitbucket#master"
            type: "bitbucket-notify"                   

### Pipeline-specific

To use on a single pipeline, update your pipeline to include a new `resource_types` entry...

    resource_types:
      - name: "bitbucket-notify"
        type: "docker-image"
        source:
          repository: "karunamon/concourse-resource-bitbucket"
          tag: "master"


## References

 * [Resources (concourse.ci)](https://concourse.ci/resources.html)
 * [Bitbucket build status API](https://developer.atlassian.com/bitbucket/server/docs/latest/how-tos/updating-build-status-for-commits.html)


## Thanks

* [Danny Berger (aka dpb587)](https://github.com/dpb587) for his well-written and easy to follow [github-status-resource](https://github.com/dpb587/github-status-resource), which was essential to understanding the ins and outs of Concourse resources, as well as providing the layout for this document.
* [People of the Concourse Slack Channel](https://concourseci.slack.com/messages/general/), in specific, `robdimsdale`, `jtarchie`, `greg`, and `vito`, for patiently helping a clueless newbie understand a complex system.

## License

[Apache License v2.0]('./LICENSE')
