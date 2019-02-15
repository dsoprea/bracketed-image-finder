[![Build Status](https://travis-ci.org/dsoprea/bracketed_image_finder.svg?branch=master)](https://travis-ci.org/dsoprea/bracketed_image_finder)
[![Coverage Status](https://coveralls.io/repos/github/dsoprea/bracketed_image_finder/badge.svg?branch=master)](https://coveralls.io/github/dsoprea/bracketed_image_finder?branch=master)


# Overview

Some cameras support taking bracketed pictures. Bracketing is an operation that rapidly takes a series of pictures with slight variations. This can be used for producing HDR pictures as well as allowing you to experiment in situations where the conditions may be tricky or rapidly changing with what the current conditions might require or to save time in the present by taking a bunch of pictures that will likely include at least one good one at the expense of having to spend more time later sifting through the extra images.

This project will recursively scan through the JPEG images under a given path and identify sequential sequences of exposure-bracketed images.


# Installation

This project requires Python 3. To install:

```
$ pip install bracketed_images_finder
```


# Sequence Identification

The library currently identifies exposure-based bracketing.

Requirements:

- Images have a "exposure mode" of (2) ("auto bracketed")
- Images consist of three, five, or seven images
- Sorting the filenames in increasing order will also sort them in chronologically-increasing order

The actual exposure deltas do not matter. Even when configured as a specific value, we have seen the effective exposures being different then expected.

The library currently recognizes the following exposure sequences:

## 0, -, +

Exposure start at the current, default exposure and are followed by one or more pairs of lower-higher values of the same magnitude, where the magnitude progressively increases for each additional pair. Referred to as a "periodic exposure" sequence.

## -, 0, +

Exposures increase from a lower exposure value to a higher exposure value, where both are the same distance from the current, default exposure. Referred to as a "sequential exposure" sequence.


# Output

The output is printed either as parseable text or JSON:

```
$ bif_find tests/assets/images
periodic DSC08196.JPG DSC08197.JPG DSC08198.JPG DSC08199.JPG DSC08200.JPG
periodic DSC08201.JPG DSC08202.JPG DSC08203.JPG DSC08204.JPG DSC08205.JPG

$ bif_find tests/assets/images --json
[
    {
        "entries": [
            {
                "exposure_value": 0.0,
                "rel_filepath": "DSC08196.JPG",
                "timestamp": "2019-02-13T00:31:50"
            },
            {
                "exposure_value": -0.7,
                "rel_filepath": "DSC08197.JPG",
                "timestamp": "2019-02-13T00:31:50"
            },
            {
                "exposure_value": 0.7,
                "rel_filepath": "DSC08198.JPG",
                "timestamp": "2019-02-13T00:31:50"
            },
            {
                "exposure_value": -1.3,
                "rel_filepath": "DSC08199.JPG",
                "timestamp": "2019-02-13T00:31:50"
            },
            {
                "exposure_value": 1.3,
                "rel_filepath": "DSC08200.JPG",
                "timestamp": "2019-02-13T00:31:51"
            }
        ],
        "type": "periodic"
    },
    {
        "entries": [
            {
                "exposure_value": 0.0,
                "rel_filepath": "DSC08201.JPG",
                "timestamp": "2019-02-13T00:32:09"
            },
            {
                "exposure_value": -0.7,
                "rel_filepath": "DSC08202.JPG",
                "timestamp": "2019-02-13T00:32:09"
            },
            {
                "exposure_value": 0.7,
                "rel_filepath": "DSC08203.JPG",
                "timestamp": "2019-02-13T00:32:10"
            },
            {
                "exposure_value": -1.3,
                "rel_filepath": "DSC08204.JPG",
                "timestamp": "2019-02-13T00:32:10"
            },
            {
                "exposure_value": 1.3,
                "rel_filepath": "DSC08205.JPG",
                "timestamp": "2019-02-13T00:32:10"
            }
        ],
        "type": "periodic"
    }
]
```
