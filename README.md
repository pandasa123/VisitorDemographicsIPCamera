# Capturing Visitor Demographic Data through IP Camera Video Frames

## Introduction

This semester, I took a course in Museum Studies at the University of Michigan (Ann Arbor). As a second year Computer Engineering major, I tried to understand how museum visitor experience could be enhanced through the use of technology and realised that the Museum has no automated method to track visitor demographics.

## Project goals

* Collect demographic data
* Collect facial sentiment data
* Visualise sentiment data to improve user experience

## Proposed Architecture

Based on Moataz Anany's [Video Analyser](https://github.com/awslabs/amazon-rekognition-video-analyzer). Expanding on the original architecture, I adjusted various aspects to collect demographic data from AWS Rekognition, process and send to the user demo UI and to AWS Quicksight for rich visualisations

My architecure is located in the root directory of the project (```/architecure.png```)
![Architecture](https://gitlab.eecs.umich.edu/pandasa/VisitorDemographicsIPCamera/blob/master/architecture.png)

## How start demo

1) [Sign up for AWS and create and Admin user](http://docs.aws.amazon.com/lambda/latest/dg/setting-up.html)

2) Install Python 2.7+ and Pip

3) Create a [Python Virtual Environment](https://virtualenv.pypa.io/en/stable/)
  * ``` virtualenv ENV ```
  * ``` source bin/activate env ```

4) Use Pip to [install AWS CLI ](http://docs.aws.amazon.com/cli/latest/userguide/installing.html). [Configure AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) for an IAM user in us-east-1 and create an IAM user with access to:
  * Amazon S3
  * Amazon DynamoDB
  * Amazon Kinesis
  * Amazon Firehose
  * Amazon CloudWatch
  * Amazon Cloudformation
  * Amazon Rekognition
  * Amazon API Gateway
  * Creating IAM Roles

  6) Clone repo
  5) Use Pip to install OpenCV 3, Boto3 , Pynt
  6) ``` pip install pytz ```
  7) ``` pip install pytz -t <path-to-project-dir>/lambda/imageprocessor/  ```

## Configuring the project (from Moataz Anany)
> **NOTE: You must set the value of any parameter that has the tag NO-DEFAULT**

### config/global-params.json

Specifies “global” build configuration parameters. It is read by multiple build scripts.

```json
{
    "StackName" : "video-analyzer-stack"
}
```
Parameters:

* `StackName` - The name of the stack to be created in your AWS account.

### config/cfn-params.json
Specifies and overrides default values of AWS CloudFormation parameters defined in the template (located at aws-infra/aws-infra-cfn.yaml). This file is read by a number of build scripts, including ```createstack```, ```deploylambda```, and ```webui```.

```json
{
    "SourceS3BucketParameter" : "<NO-DEFAULT>",
    "ImageProcessorSourceS3KeyParameter" : "src/lambda_imageprocessor.zip",
    "FrameFetcherSourceS3KeyParameter" : "src/lambda_framefetcher.zip",

    "FrameS3BucketNameParameter" : "<NO-DEFAULT>",

    "FrameFetcherApiResourcePathPart" : "enrichedframe",
    "ApiGatewayRestApiNameParameter" : "VidAnalyzerRestApi",
    "ApiGatewayStageNameParameter": "development",
    "ApiGatewayUsagePlanNameParameter" : "development-plan"
}
```
Parameters:

* `SourceS3BucketParameter` - The Amazon S3 bucket to which your AWS Lambda function packages (.zip files) will be dpeloyed. If a bucket with such a name does not exist, the `deploylambda` build command will create it for you with appropriate permissions. AWS CloudFormation will access this bucket to retrieve the .zip files for Image Processor and Frame Fetcher AWS Lambda functions.

* `ImageProcessorSourceS3KeyParameter` - The Amazon S3 key under which the Image Processor function .zip file will be stored.

* `FrameFetcherSourceS3KeyParameter` - The Amazon S3 key under which the Frame Fetcher function .zip file will be stored.

* `FrameS3BucketNameParameter` - The Amazon S3 bucket that will be used for storing video frame images.

* `FrameFetcherApiResourcePathPart` - The name of the Frame Fetcher API resource path part in the API Gateway URL.

* `ApiGatewayRestApiNameParameter` - The name of the API Gateway REST API to be created by AWS CloudFormation.

* `ApiGatewayStageNameParameter` - The name of the API Gateway stage to be created by AWS CloudFormation.

* `ApiGatewayUsagePlanNameParameter` - The name of the API Gateway usage plan to be created by AWS CloudFormation.


### config/imageprocessor-params.json
Specifies configuration parameters to be used at run-time by the Image Processor lambda function. This file is packaged along with the Image Processor lambda function code in a single .zip file using the `packagelambda` build script.

```json
{
	"s3_bucket" : "<NO-DEFAULT>",
	"s3_key_frames_root" : "frames/",

	"ddb_table" : "EnrichedFrame",

	"rekog_max_labels" : 123,
    "rekog_min_conf" : 50.0,

	"label_watch_list" : ["Human", "Pet", "Bag", "Toy"],
	"label_watch_min_conf" : 90.0,
	"label_watch_phone_num" : "",
	"label_watch_sns_topic_arn" : "",
	"timezone" : "US/Eastern"
}
```

* `s3_bucket` - The Amazon S3 bucket in which Image Processor will store captured video frame images. The value specified here _must_ match the value specified for the `FrameS3BucketNameParameter` parameter in the `cfn-params.json` file.

* `s3_key_frames_root` - The Amazon S3 key prefix that will be prepended to the keys of all stored video frame images.

* `ddb_table` - The Amazon DynamoDB table in which Image Processor will store video frame metadata. The default value,`EnrichedFrame`, matches the default value of the AWS CloudFormation template parameter `DDBTableNameParameter` in the `aws-infra/aws-infra-cfn.yaml` template file.

* `rekog_max_labels` - The maximum number of labels that Amazon Rekognition can return to Image Processor.

* `rekog_min_conf` - The minimum confidence required for a label identified by Amazon Rekognition. Any labels with confidence below this value will not be returned to Image Processor.

* `label_watch_list` - A list of labels for to watch out for. If any of the labels specified in this parameter are returned by Amazon Rekognition, an SMS alert will be sent via Amazon SNS. The label's confidence must exceed `label_watch_min_conf`.

* `label_watch_min_conf` - The minimum confidence required for a label to trigger a Watch List alert.

* `label_watch_phone_num` - The mobile phone number to which a Watch List SMS alert will be sent. Does not have a default value. **You must configure a valid phone number adhering to the E.164 format (e.g. +1404XXXYYYY) for the Watch List feature to become active.**

* `label_watch_sns_topic_arn` - The SNS topic ARN to which you want Watch List alert messages to be sent. The alert message contains a notification text in addition to a JSON formatted list of Watch List labels found. This can be used to publish alerts to any SNS subscribers, such as Amazon SQS queues.

* `timezone` - The timezone used to report time and date in SMS alerts. By default, it is "US/Eastern". See this list of [country codes, names, continents, capitals, and pytz timezones](https://gist.github.com/pamelafox/986163)).

## Building the project (from Moataz Anany)
## Build commands

This section describes important build commands and how to use them. If you want to use these commands right away to build the prototype, you may skip to the section titled _"Deploy and run the prototype"_.

### The `packagelambda` build command

Run this command to package the prototype's AWS Lambda functions and their dependencies (Image Processor and Frame Fetcher) into separate .zip packages (one per function). The deployment packages are created under the `build/` directory.

```bash
pynt packagelambda # Package both functions and their dependencies into zip files.

pynt packagelambda[framefetcher] # Package only Frame Fetcher.
```

Currently, only Image Processor requires an external dependency, [pytz](http://pytz.sourceforge.net/). If you add features to Image Processor or Frame Fetcher that require external dependencies, you should install the dependencies using Pip by issuing the following command.

```bash
pip install <module-name> -t <path-to-project-dir>/lambda/<lambda-function-dir>
```
For example, let's say you want to perform image processing in the Image Processor Lambda function. You may decide on using the [Pillow](http://pillow.readthedocs.io/en/3.0.x/index.html) image processing library. To ensure Pillow is packaged with your Lambda function in one .zip file, issue the following command:

```bash
pip install Pillow -t <path-to-project-dir>/lambda/imageprocessor #Install Pillow dependency
```

You can find more details on installing AWS Lambda dependencies [here](http://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html).

### The `deploylambda` build command

Run this command before you run `createstack`. The ```deploylambda``` command uploads Image Processor and Frame Fetcher .zip packages to Amazon S3 for pickup by AWS CloudFormation while creating the prototype's stack. This command will parse the deployment Amazon S3 bucket name and keys names from the cfn-params.json file. If the bucket does not exist, the script will create it. This bucket must be in the same AWS region as the AWS CloudFormation stack, or else the stack creation will fail. Without parameters, the command will deploy the .zip packages of both Image Processor and Frame Fetcher. You can specify either “imageprocessor” or “framefetcher” as a parameter between square brackets to deploy an individual function.

Here are sample command invocations.

```bash
pynt deploylambda # Deploy both functions to Amazon S3.

pynt deploylambda[framefetcher] # Deploy only Frame Fetcher to Amazon S3.
```

### The `createstack` build command
The createstack command creates the prototype's AWS CloudFormation stack behind the scenes by invoking the `create_stack()` API. The AWS CloudFormation template used is located at aws-infra/aws-infra-cfn.yaml under the project’s root directory. The prototype's stack requires a number of parameters to be successfully created. The createstack script reads parameters from both global-params.json and cfn-params.json configuration files. The script then passes those parameters to the `create_stack()` call.

Note that you must, first, package and deploy Image Processor and Frame Fetcher functions to Amazon S3 using the `packagelambda` and `deploylambda` commands (documented later in this guid) for the AWS CloudFormation stack creation to succeed.

You can issue the command as follows:

```bash
pynt createstack
```

Stack creation should take only a couple of minutes. At any time, you can check on the prototype's stack status either through the AWS CloudFormation console or by issuing the following command.

```bash
pynt stackstatus
```

Congratulations! You’ve just created the prototype's entire architecture in your AWS account.


### The `deletestack` build command

The `deletestack` command, once issued, does a few things.
First, it empties the Amazon S3 bucket used to store video frame images. Next, it calls the AWS CloudFormation delete_stack() API to delete the prototype's stack from your account. Finally, it removes any unneeded resources not deleted by the stack (for example, the prototype's API Gateway Usage Plan resource).

You can issue the `deletestack` command as follows.

```bash
pynt deletestack
```

As with `createstack`, you can monitor the progress of stack deletion using the `stackstatus` build command.

### The `deletedata` build command

The `deletedata` command, once issued, empties the Amazon S3 bucket used to store video frame images. Next, it also deletes all items in the DynamoDB table used to store frame metadata.

Use this command to clear all previously ingested video frames and associated metadata. The command will ask for confirmation [Y/N] before proceeding with deletion.

You can issue the `deletedata` command as follows.

```bash
pynt deletedata
```

### The `stackstatus` build command

The `stackstatus` command will query AWS CloudFormation for the status of the prototype's stack. This command is most useful for quickly checking that the prototype is up and running (i.e. status is "CREATE\_COMPLETE" or "UPDATE\_COMPLETE") and ready to serve requests from the Web UI.

You can issue the command as follows.


```bash
pynt stackstatus # Get the prototype's Stack Status
```


### The `webui` build command

Run this command when the prototype's stack has been created (using `createstack`). The webui command “builds” the Web UI through which you can monitor incoming captured video frames. First, the script copies the webui/ directory verbatim into the project’s build/ directory. Next, the script generates an apigw.js file which contains the API Gateway base URL and the API key to be used by Web UI for invoking the Fetch Frames function deployed in AWS Lambda. This file is created in the Web UI build directory.

You can issue the Web UI build command as follows.

```bash
pynt webui
```

### The `webuiserver` build command

The webuiserver command starts a local, lightweight, Python-based HTTP server on your machine to serve Web UI from the build/web-ui/ directory. Use this command to serve the prototype's Web UI for development and demonstration purposes. You can specify the server’s port as pynt task parameter, between square brackets.

Here’s sample invocation of the command.

```bash
pynt webuiserver # Starts lightweight HTTP Server on port 8080.
```

### The `videocaptureip` and `videocapture` build commands

The videocaptureip command fires up the MJPEG-based video capture client (source code under the client/ directory). This command accepts, as parameters, an MJPEG stream URL and an optional frame capture rate. The capture rate is defined as 1 every X number of frames. Captured frames are packaged, serialized, and sent to the Kinesis Frame Stream. The video capture client for IP cameras uses Open CV 3 to do simple image processing operations on captured frame images – mainly image rotation.

Here’s a sample command invocation.

```bash
pynt videocaptureip["http://192.168.0.2/video",20] # Captures 1 frame every 20.
```

On the other hand, the videocapture command (without the trailing 'ip'), fires up a video capture client that captures frames from a camera attached to the machine on which it runs. If you run this command on your laptop, for instance, the client will attempt to access its built-in video camera. This video capture client relies on Open CV 3 to capture video from physically connected cameras. Captured frames are packaged, serialized, and sent to the Kinesis Frame Stream.

Here’s a sample invocation.

```bash
pynt videocapture[20] # Captures one frame every 20.
```

## Deploy and run the prototype
In this section, we are going use project's build commands to deploy and run the prototype in your AWS account. We’ll use the commands to create the prototype's AWS CloudFormation stack, build and serve the Web UI, and run the Video Cap client.

* Prepare your development environment, and ensure configuration parameters are set as you wish.

* On your machine, in a command line terminal change into the root directory of the project. Activate your virtual Python environment. Then, enter the following commands:

```bash
$ pynt packagelambda #First, package code & configuration files into .zip files

#Command output without errors

$ pynt deploylambda #Second, deploy your lambda code to Amazon S3

#Command output without errors

$ pynt createstack #Now, create the prototype's CloudFormation stack

#Command output without errors

$ pynt webui #Build the Web UI

#Command output without errors
```

* On your machine, in a separate command line terminal:

```bash
$ pynt webuiserver #Start the Web UI server on port 8080 by default
```

* In your browser, access http://localhost:8080 to access the prototype's Web UI. You should see a screen similar to this:

* Now turn on your IP camera or launch the app on your smartphone. Ensure that your camera is accepting connections for streaming MJPEG video over HTTP, and identify the local URL for accessing that stream.

* Then, in a terminal window at the root directory of the project, issue this command:

```bash
$ pynt videocaptureip["<your-ip-cam-mjpeg-url>",<capture-rate>]
```
* Or, if you don’t have an IP camera and would like to use a built-in camera:

```bash
$ pynt videocapture[<frame-capture-rate>]
```

* Few seconds after you execute this step, the dashed area in the Web UI will auto-populate with captured frames, side by side with labels recognized in them.

## Exporting DynamoDB to Quicksight
* Follow AWS documentation on [how to export DynamoDB Tables to CSV](http://docs.aws.amazon.com/datapipeline/latest/DeveloperGuide/dp-importexport-ddb-part2.html)
* Import CSV into Quicksight

## Future Improvements

I had a very little time to work on the project but, for the next iteration of this project, I hope to:
* Package DynamoDB to CSV into this project properly
* Perhaps move away from DynamoDB entirely to have a seamless Quicksight experience
* Add SNS to alert when visitor sentiment is critical
* Use more robust recognition and sentiment packages
* Reduce latency

## Acknowledgements
* Moataz Anany for [Video Analyser](https://github.com/awslabs/amazon-rekognition-video-analyzer), under Amazon Software License
