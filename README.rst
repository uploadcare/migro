.. raw:: html

    <p align="center">
      <a href="https://uploadcare.com/?ref=github-readme">
        <picture>
          <source media="(prefers-color-scheme: light)" srcset="https://ucarecdn.com/1b4714cd-53be-447b-bbde-e061f1e5a22f/logosafespacetransparent.svg">
          <source media="(prefers-color-scheme: dark)" srcset="https://ucarecdn.com/3b610a0a-780c-4750-a8b4-3bf4a8c90389/logotransparentinverted.svg">
          <img width=250 alt="Uploadcare logo" src="https://ucarecdn.com/1b4714cd-53be-447b-bbde-e061f1e5a22f/logosafespacetransparent.svg">
        </picture>
      </a>
    </p>
    <p align="center">
      <a href="https://uploadcare.com?ref=github-readme">Website</a> •
      <a href="https://uploadcare.com/docs/start/quickstart?ref=github-readme">Quick Start</a> •
      <a href="https://uploadcare.com/docs?ref=github-readme">Docs</a> •
      <a href="https://uploadcare.com/blog?ref=github-readme">Blog</a> •
      <a href="https://discord.gg/mKWRgRsVz8?ref=github-readme">Discord</a> •
      <a href="https://twitter.com/Uploadcare?ref=github-readme">Twitter</a>
    </p>

================================
MIGRO: Uploadcare Migration Tool
================================


Migro assists in migrating files to Uploadcare from AWS S3 and other cloud
file management services such as Filestack, Cloudinary, etc.
You can also migrate from additional services by providing URLs for file import.

Migro utilizes a local SQLite database to store migration statuses to prevent duplicates,
thereby avoiding re-uploading files in case of an interruption or failure.


How migration works
-------------------

Migro does not directly download any files. Instead, it utilizes
the `Uploading API`_, specifically the ``From URL`` method_.
The migration process is straightforward: you either provide a list of file
URLs or set your AWS S3 credentials, and those files are uploaded to your Uploadcare project.

Upon completion, you will receive a listing of all uploaded files.
You will also receive details on the status of each processed file and any errors that may have occurred.


Installation
------------

This utility requires Python version 3.8 or later.

In order to install ``migro``, run:

.. code-block:: console

  $ pip install uploadcare-migro


Get started
-----------

To begin using Migro, you must have your Uploadcare project `public key`_.

Optionally, you can store the public key and other necessary credentials in environment variables.
This approach is beneficial if you must migrate many files, allowing you to perform multiple migrations efficiently.

.. code-block:: console

  $ migro init <OPTIONS>

After running the initialization command, your credentials will be saved in a local ``.env``
file, allowing you to use Migro without specifying them in the command line each time.
Once the ``.env`` file is created, you can edit it manually if needed.

.. code-block:: console

  $ migro init --public_key <PUBLIC_KEY> --secret_key <SECRET_KEY>

If you run the command twice or more times, the tool will update the existing
credentials or add new ones. For instance, if you run the following command:

.. code-block:: console

  $ migro init --secret_key <SECRET_KEY>

The tool will update the secret key but leave the public key unchanged.

Different credentials are needed depending on the source of files you want to migrate.
Refer to the necessary options for each source below.


Migrating files
---------------

Migro supports migration from the following sources:

- AWS S3: The tool scans the bucket, generates temporary signed URLs, and migrates all files.
- File with URLs: The tool reads a file containing URLs and migrates all files listed.

Each migration source requires the following arguments:

``<PUBLIC_KEY>`` — your Uploadcare project `public key`_.

``[<SECRET_KEY>]`` — your Uploadcare project secret key.
This is optional and required only if the signed uploads feature is enabled in your project.

And the following options:

.. code-block::

  --upload_base_url TEXT            Base URL for uploads.  [default:
                                    https://upload.uploadcare.com/]

  --upload_timeout FLOAT            Number of seconds to wait till the file will be
                                    processed by `from_url` upload.  [default: 30]

  --concurrent_uploads INTEGER      Maximum number of upload requests running in
                                    'parallel'.  [default: 20]

  --status_check_interval FLOAT     Number of seconds in between status check
                                    requests.

Each option can be preset using the `migro init` command.


Usage with AWS S3
-----------------

How it works:
  1. Migro verifies the credentials provided and checks if the bucket policy is correct.
  2. The tool then scans the bucket and generates temporary signed URLs for all files.
  3. Migro proceeds to upload all files to Uploadcare.


Set policy for a bucket
~~~~~~~~~~~~~~~~~~~~~~~

To ensure proper functionality, set the following minimal permissions for your AWS S3 bucket policy:

.. code-block::

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::<YOUR BUCKET NAME>",
                    "arn:aws:s3:::<YOUR BUCKET NAME>/*"
                ]
            }
        ]
    }

Remember to replace <YOUR BUCKET NAME> with your actual bucket name.

To initiate the migration, execute the following command:

.. code-block:: console

    $ migro s3 <BUCKET_NAME> <PUBLIC_KEY> [<SECRET_KEY>] [<OPTIONS>]

For example:

.. code-block:: console

    $ migro s3 <BUCKET_NAME> <PUBLIC_KEY> --s3_access_key_id <ACCESS_KEY_ID> --s3_secret_access_key <SECRET_ACCESS_KEY> --s3_region <REGION>


Options:

.. code-block::


  -h, --help                        Show this help and quit.

  --s3_access_key_id STRING         AWS Access Key ID for accessing the S3 bucket.

  --s3_secret_access_key STRING     AWS Secret Access Key for accessing the S3 bucket.

  --s3_region STRING                AWS region where the S3 bucket is located.

Each option can be set beforehand using the `migro init` command.

Note:
    Utilizing ``boto3``, Migro attempts to use the
    `default AWS credentials <https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials>`_
    when they are not specified during the initialization step or via command line.


Usage with file list
--------------------

To migrate files using a list of URLs, execute the following command:

.. code-block:: console

    $ migro urls <INPUT_FILE> [<PUBLIC_KEY>] [<SECRET_KEY>]

Where:

``<INPUT_FILE>`` — path to a text file containing a list of file URLs
to be uploaded to your Uploadcare project.

Options:

.. code-block::

  -h, --help                  Show this help and quit.


Results file
------------

Once the migration is complete, you'll receive a ``.csv`` file containing the results,
which will be located in the logs folder.

.. code-block::

    Path                , File Size, Uploadcare UUID                       , Status  , Error
    ------------------- , ---------, ------------------------------------- , ------- , ----------------------------------------------------------------------
    kittens.jpg         , 3478134  , 0897e21a-7b7f-4037-95ec-9b70cbdf6d30  , uploaded,
    raccoons.jpg        , 2063823  , 14af9b5a-5388-4f48-a38b-61380e8c7332  , uploaded,
    invalid_format.csv  , 339898   ,                                       , error   , "File validation error: Uploading of these file types is not allowed."


The output file format is straightforward. Each line represents an input file, with five columns separated by commas.

Column Details:
 * The first column contains the input file URL or S3 key.
 * The second column displays the file size in bytes.
 * The third column holds the uploaded file UUID or remains empty if the file was not uploaded.
 * The fourth column indicates the status of the file, which can be "uploaded" or "error".
 * The fifth column provides an error message if the file was not uploaded.


Examples
--------

Here's how you set up the tool for the first time:

.. code-block:: console

    $ migro init --public_key <PUBLIC_KEY> --s3_access_key_id <S3_ACCESS_KEY> --s3_secret_access_key <S3_SECRET_KEY> --s3_bucket_name <S3_BUCKET_NAME> --s3_region <S3_REGION>

.. code-block::

    Configuration saved successfully to /Users/username/path/to/migro/.env

and run the utility:

.. code-block:: console

    $ migro s3

And that's what you get:

.. code-block::

    Checking the credentials...
    Credentials are correct.
    Collecting files...
    Starting upload...


    Upload progress: 100%|████████████████████████████████████████████████| 6/6 [00:03<00:00,  1.74s/file]
    File uploading has been finished!
    Uploaded files: 5
    Failed files: 1
    Check the results in "/Users/username/path/to/migro/logs/Attempt 1 - 2024-04-23 17-13-38 - s3.csv"
    Thanks for your interest in Uploadcare.
    Hit us up at help@uploadcare.com in case of any questions.


After the migration
-------------------

Once the migration is complete, execute the ``migro drop`` command to
remove the `.env` file containing credentials, clear the local database, and the logs folder.

.. code-block:: console

    $ migro drop


Note for Windows users
----------------------

Currently, there is an issue with terminating the program using CTRL+C on Windows.
As a result, the program cannot be terminated correctly using this method.

This issue stems from platform-dependent behavior in the Python programming language.


Alternatives
------------

You can use our libs_
to migrate your files from any source.

.. _Uploading API: https://uploadcare.com/documentation/upload/
.. _method: https://uploadcare.com/documentation/upload/#from-url
.. _public key: https://uploadcare.com/documentation/keys/
.. _libs: https://uploadcare.com/documentation/libs/


Need help?
----------

Do you need to migrate files from another service? Feel free to create an issue.
Alternatively, you can reach us at help@uploadcare.com.
We'll be happy to assist you with the migration.
