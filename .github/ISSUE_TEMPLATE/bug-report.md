name: Bug Report
description: Report a bug
title: "[Bug] "
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        ## Bug Description
        ## Steps to Reproduce
        ## Environment
  - type: checkboxes
    attributes:
      label: Confirm
      options:
        - label: I have searched existing issues
          required: true