
<?php
function generate_access_token($params){
    if (authenticate_shopify_request($params)) {
        // Set variables for our request
        $query = [
            "client_id" => $api_key, // Your API key
            "client_secret" => $shared_secret, // Your app credentials (secret key)
            "code" => $params["code"], // Grab the access key from the URL
        ];

        // Generate access token URL
        $access_token_url ="https://" . $params["shop"] . "/admin/oauth/access_token";

        // Configure curl client and execute request
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($ch, CURLOPT_URL, $access_token_url);
        curl_setopt($ch, CURLOPT_POST, count($query));
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($query));
        $result = curl_exec($ch);
        curl_close($ch);

        // Store the access token
        $result = json_decode($result, true);
        $access_token = $result["access_token"];

        return $access_token;
    }

    return NULL;
}
?>
