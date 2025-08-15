## 各種環境情報

|項目|値|補足|
|-|-|-|
|ユーザーネーム|gb86sub|IAM Identity Centerで割り当てたユーザ|
コンソールサインイン URL|https://d-9567bf36fa.awsapps.com/start|IAM Identity Center 上記ユーザのログインURL|

## aws sso 初期設定
```shell
% aws configure sso
SSO session name (Recommended): [username]
SSO start URL [None]: https://[see IAM Identity Center].awsapps.com/start
SSO region [None]: ap-northeast-1
SSO registration scopes [sso:account:access]: sso:account:access
...
Default client Region [None]: ap-northeast-1
CLI default output format (json if not specified) [None]:
Profile name [~]: [username]
To use this profile, specify the profile name using --profile, as shown:
```

```shell
aws sso login --profile [username]
```

## 参考リンク

**IAM Identity Centerの設定**

[AWSアカウントにサインインするときはIAM Identity Center経由にしましょう](https://zenn.dev/murakami_koki/articles/79ac2456564b36)

**SSO Login設定**
[AWS CLIのSSO設定](https://zenn.dev/fez_tech/articles/fec83b79c44ff1)