#!/bin/bash
printf '%s\n' examples/*.py | xargs -n1 python
