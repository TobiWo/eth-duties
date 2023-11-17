# Mode

The default running mode of `eth-duties` is logging duties to the console (specified with value `log`). However, professional node operators or advanced home stakers might leverage the tool in their cicd pipelines to e.g. prevent an unintentional client update when your validator is right before proposing a block or part of the sync committee. This is where the different `cicd` modes come into play. You can make your deployment job dependent from the `eth-duties` job so that the deployment job will only run when `eth-duties` exits gracefully with `exit code 0`. This documentation will not go into detail about advanced pipelines in gitlab or github. However, I provide a separate `cicd-compose.yaml` (in docker folder) which may be adopted by home stakers.

**Note** If you do not omit attestation duties with `--omit-attestation-duties` these are also considered as valid duties for the cicd modes. For a more fine granular setting on attestation duties please check the [chapter about --mode-cicd-attestation-time and --mode-cicd-attestation-proportion](#mode-cicd-attestation-time-and-mode-cicd-attestation-proportion)

## What are relevant duties

In the following sub chapters I will often refer to relevant duties. This is a short explanation. Relevant are:

* validator is in current sync committee
* validator is in next sync committee
* validator will propose a block
* x of y attestation duties (while y == number of validators monitored) need to be executed in less than a defined time threshold
    * see [chapter about --mode-cicd-attestation-time and --mode-cicd-attestation-proportion](#mode-cicd-attestation-time-and-mode-cicd-attestation-proportion)

## Modes

### cicd-exit

This mode results in a one time check whether one of your supplied validators has an relevant upcoming duty. If there is one the tool exits with `exit code 1`. If there is none the tool exits with `exit code 0`.

### cicd-wait

This mode results in an ongoing process (similar to the standard behavior) where `eth-duties` checks for relevant upcoming duties until there is none. If there will be no relevant upcoming duty the application exits with `exit code 0`. Compared to the standard logging behavior this process only runs for a certain amount of time (specified with flag `--mode-cicd-waiting-time` (default: 780 seconds, approx. 2 epochs)). If this timeframe ends, `eth-duties` exits with `exit code 1`.

### cicd-force-graceful-exit

This mode results in an immediate graceful exit with `exit code 0` without checking for duties. The rationale behind this flag is the following: If your deployment job will not run because of upcoming duties but you need to force an update for whatever reason you can use the mode `cicd-force-graceful-exit`. I'm not an expert in github pipelines but in gitlab you can prefill environment variables when you start a pipeline manually via the web ui. This way you don't need to adapt your pipeline code but just restart a pipeline with the `cicd-force-graceful-exit` mode. In general how to setup your pipelines is out of scope of this documentation. For more information please check the respective platform documentation. For gitlab this would be [the following website](https://docs.gitlab.com/ee/ci/pipelines/index.html#prefill-variables-in-manual-pipelines).

## mode-cicd-attestation-time and mode-cicd-attestation-proportion

These flags can be specifically useful for home stakers with a small amount of validators while using any cicd mode (`cicd-exit` or `cicd-wait`). The idea is that a home staker with a small amount of validators most often handles attestation duties and it might be hard to figure out manually when to perform e.g. a client update so that you only miss the minimum amount of attestation duty rewards or even none. **It is important to note that upcoming sync-committee or block proposal duties are considered relevant in any way. This means `eth-duties` will always exits non-gracefully in mode `cicd-exit` and `cicd-wait` (when waiting threshold is reached) while one of these relevant duties is in the queue. In other words if your settings for monitoring attesation duties are matched it will get ignored when another relevant duty is in the queue.**

In general both flags refer to the fact that `eth-duties` will exit gracefully when the defined proportion of attestion duties will be executed after the provided time threshold. Let's check an example to get a better understanding. We assume a home staker who runs 10 validators:

* You want to exit `eth-duties` gracefully when 8/10 validator attestation duties need to be executed in 4 minutes or later:

    ```bash
    --mode cicd-wait --mode-cicd-attestation-time 240 --mode-cicd-attestation-proportion 0.8
    ```

For more clarity please check the `cicd-attestation-compose.yaml` within the docker folder.

These new flags will be only useful until a certain threshold of monitored validators is reached. This is because the higher the number of validators monitored the smaller the probability that a defined proportion of validator attestation duties will happen at a specified time in the future or later. To be more precise let's consider you monitor 30 validators. If you set the new flags to `--mode-cicd-attestation-time 240 --mode-cicd-attestation-proportion 0.8` it might never happen that 80% of attestation duties need to be performed in 4 minutes or later. You could reduce the proportion or/and time value but at some point these will not bring any value for you. You need to test a little bit what could be a good setting for your setup.
