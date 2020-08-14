# f5_rest_api_pool_via_cli_script_tester

intent of this script is to compare pool add/remove operations via an iControl REST transaction that includes a bunch of individual iControl REST requests that add one member at a time, followed by submitting the transaction. Alternative approach is to leverage a tmsh cli script that can be accesed via iControl REST
