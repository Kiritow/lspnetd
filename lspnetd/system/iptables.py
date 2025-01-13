import subprocess
from lspnetd.common.utils import sudo_wrap, sudo_call
from lspnetd.common.logger import get_logger


logger = get_logger("iptables")


def try_create_iptables_chain(table_name: str, chain_name: str):
    try:
        subprocess.run(sudo_wrap(["iptables", "-t", table_name, "-N", chain_name]), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        if 'iptables: Chain already exists.' not in e.stderr:
            raise

        logger.info(f"iptables chain {chain_name} exists in {table_name} table, skip creation.")


def try_append_iptables_rule(table_name: str, chain_name: str, rule_args: list[str]):
    try:
        subprocess.run(sudo_wrap(["iptables", "-t", table_name, "-C", chain_name] + rule_args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        if 'iptables: Bad rule (does a matching rule exist in that chain?)' not in e.stderr and 'iptables: No chain/target/match by that name' not in e.stderr:
            raise

        logger.info(f"iptables rule not exist, adding: iptables -t {table_name} -A {chain_name} {' '.join(rule_args)}")
        sudo_call(["iptables", "-t", table_name, "-A", chain_name] + rule_args)


def try_insert_iptables_rule(table_name: str, chain_name: str, rule_args: list[str]):
    try:
        subprocess.run(sudo_wrap(["iptables", "-t", table_name, "-C", chain_name] + rule_args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        if 'iptables: Bad rule (does a matching rule exist in that chain?)' not in e.stderr and 'iptables: No chain/target/match by that name' not in e.stderr:
            raise

        logger.info(f"iptables rule not exist, adding: iptables -t {table_name} -I {chain_name} {' '.join(rule_args)}")
        sudo_call(["iptables", "-t", table_name, "-I", chain_name] + rule_args)


def try_flush_iptables_chain(table_name: str, chain_name: str):
    try:
        sudo_call(["iptables", "-t", table_name, "-F", chain_name])
    except subprocess.CalledProcessError as e:
        logger.warning(f"Error occured when flush iptables chain {chain_name} table {table_name}, skipping... ({e.stderr})")


def ensure_custom_iptables(prefix: str):
    try_create_iptables_chain("nat", f"{prefix}-POSTROUTING")
    try_insert_iptables_rule("nat", "POSTROUTING", ["-j", "{}-POSTROUTING".format(prefix)])

    try_create_iptables_chain("nat", f"{prefix}-PREROUTING")
    try_insert_iptables_rule("nat", "PREROUTING", ["-j", "{}-PREROUTING".format(prefix)])

    try_create_iptables_chain("raw", f"{prefix}-PREROUTING")
    try_insert_iptables_rule("raw", "PREROUTING", ["-j", "{}-PREROUTING".format(prefix)])

    try_create_iptables_chain("mangle", f"{prefix}-POSTROUTING")
    try_insert_iptables_rule("mangle", "POSTROUTING", ["-j", "{}-POSTROUTING".format(prefix)])

    try_create_iptables_chain("filter", f"{prefix}-FORWARD")
    try_insert_iptables_rule("filter", "FORWARD", ["-j", "{}-FORWARD".format(prefix)])

    try_create_iptables_chain("filter", f"{prefix}-INPUT")
    try_insert_iptables_rule("filter", "INPUT", ["-j", "{}-INPUT".format(prefix)])


def clear_custom_iptables(prefix: str):
    try_flush_iptables_chain("nat", f"{prefix}-POSTROUTING")
    try_flush_iptables_chain("nat", f"{prefix}-PREROUTING")
    try_flush_iptables_chain("raw", f"{prefix}-PREROUTING")
    try_flush_iptables_chain("mangle", f"{prefix}-POSTROUTING")
    try_flush_iptables_chain("filter", f"{prefix}-FORWARD")
    try_flush_iptables_chain("filter", f"{prefix}-INPUT")


def clear_ns_iptables(namespace: str):
    try:
        sudo_call(["ip", "netns", "exec", namespace, "iptables", "-t", "nat", "-F"])
        sudo_call(["ip", "netns", "exec", namespace, "iptables", "-t", "mangle", "-F"])
        sudo_call(["ip", "netns", "exec", namespace, "iptables", "-t", "filter", "-F"])
    except subprocess.CalledProcessError as e:
        logger.warning(f"Error occured when flushing iptables in namespace {namespace}, skip... ({e.stderr})")
