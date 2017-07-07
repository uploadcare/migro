================================
MIGRO: Uploadcare migration tool
================================

Migro helps you migrate to Uploadcare from other cloud file management
services like Filestack, Cloudinary, etc.
Currently, we support migrating from Filestack, but you can migrate
from other services too: you'll just need to provide your file URLs for import.

Installation
------------

This utility requires Python 3.5.

In order to install ``migro``, simply run:

.. code-block:: console

  $ pip install uploadcare-migro


Usage
-----
.. code-block:: console

    $ migro <PUBLIC_KEY> <INPUT_FILE>

Where:

``<PUBLIC_KEY>`` — Your Uploadcare project `public key`_.

``<INPUT_FILE>`` — A text file containing a list of file URLs
to be uploaded to your Uploadcare project.

Other options:

.. code-block::

  -v, --version                   Show utility version and quit.

  -h, --help                      Show this help and quit.

  -o, --output_file PATH          Path to a Migro output file.
                                  [default: migro_result.txt]

  --upload_base TEXT              Base URL for uploads.
                                  [default: https://upload.uploadcare.com/]

  --from_url_timeout FLOAT        Maximum number of seconds for uploading
                                  a single file via `from_url`. If this
                                  threshold gets exceeded, a file is
                                  considered not loaded. Increase this
                                  timeout when expecting to get larger
                                  files via `from_url`.
                                  [default: 30]

  --max_uploads INTEGER           Maximum number of upload requests
                                  running in 'parallel'.
                                  [default: 20]

  --max_checks INTEGER            Maximum number of `from_url`
                                  status check requests running in 'parallel'.
                                  [default: 20]

  --check_interval FLOAT          Number of seconds in between status
                                  check requests.

Output file format
------------------

The output file format is quite simple.
For each input file URL or Filestack file handle, there are 3 columns divided by the \t symbol (tab).

The first column holds input file URL or Filestack handle itself,
second column — upload operation status: success or fail,
third column — output Uploadcare URL or error description.

For instance, you're willing to migrate the three following files to Uploadcare
where the first two are presented as URLs and the third one as Filestack file
handle. Also, that's how your input text file will then be structured:

.. code-block::

    https://cdn.filestackcontent.com/YBLVVdUpRqC4nOynxDd8
    https://www.facebook.com/rsrc.php/v3/y7/r/dTQOHZm7Z-3.svg
    uNWvPRXJQmO49MJbPZn9

That's what you get in your Migro output file for those input entries:

.. code-block::

    https://cdn.filestackcontent.com/YBLVVdUpRqC4nOynxDd8       success     https://ucarecdn.com/d8f8de4b-f92e-41a0-b7f9-28fd4baad9ae/
    https://www.facebook.com/rsrc.php/v3/y7/r/dTQOHZm7Z-3.svg   success     https://ucarecdn.com/4a03f3d4-2bd3-456e-89a5-008190980248/
    https://cdn.filestackcontent.com/uNWvPRXJQmO49MJbPZn9       fail        Uploading of these files types is not allowed on your current plan.

How migration works
-------------------

The migration itself is fairly simple: you provide a list of file URLs
or Filestack file handlers, and those files get uploaded to your Uploadcare
project. That's it.
Migro does not download any files. It makes use of the
`Uploading API`_.
Specifically, it utilizes the ``From URL``
method_.

As a result, you'll get a listing of all the uploaded files.
For every processed file, you're also getting its status and errors,
in case there were any.

Examples
--------

Here's how you run the utility:

.. code-block::

    $ migro 9a598e2a47fe961ea412 fileslist.txt -output_file /tmp/migro-result.txt

And that's what you get:

.. code-block::

    Upload progress: 100%|████████████████████████████████████████████████| 6/6 [00:03<00:00,  1.74s/file]
    All files have been processed, output URLs were written to: /tmp/migro-result.txt

Alternatives
------------

You can use our libs_
to migrate your files from any source.

.. _Uploading API: https://uploadcare.com/documentation/upload/
.. _method: https://uploadcare.com/documentation/upload/#from-url
.. _public key: https://uploadcare.com/documentation/keys/
.. _libs: https://uploadcare.com/documentation/libs/