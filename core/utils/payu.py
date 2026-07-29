import hashlib

def generate_payu_hash(key, txnid, amount, productinfo, firstname, email, salt):
    """
    PayU request hash:
    key|txnid|amount|productinfo|firstname|email|||||||||||salt
    """

    hash_string = (
        f"{key}|{txnid}|{amount}|{productinfo}|{firstname}|{email}"
        f"|||||||||||{salt}"
    )

    return hashlib.sha512(
        hash_string.encode("utf-8")
    ).hexdigest().lower()


def verify_payu_response_hash(post_data, salt):
    """
    PayU response hash:
    salt|status|||||||||||email|firstname|productinfo|amount|txnid|key
    """

    received_hash = post_data.get("hash", "").lower()

    key = post_data.get("key", "")
    txnid = post_data.get("txnid", "")
    amount = post_data.get("amount", "")
    productinfo = post_data.get("productinfo", "")
    firstname = post_data.get("firstname", "")
    email = post_data.get("email", "")
    status = post_data.get("status", "")

    hash_string = (
        f"{salt}|{status}|||||||||||{email}|{firstname}|"
        f"{productinfo}|{amount}|{txnid}|{key}"
    )

    calculated_hash = hashlib.sha512(
        hash_string.encode("utf-8")
    ).hexdigest().lower()

    return calculated_hash == received_hash