# Copyright 2019 VyOS maintainers and contributors <maintainers@vyos.io>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.


import os
import re

from vyos.ifconfig.interface import Interface


class VLANIf(Interface):
    """
    This class handels the creation and removal of a VLAN interface. It serves
    as base class for BondIf and EthernetIf.
    """

    default = {
        'type': 'vlan',
    }

    def __init__(self, ifname, **kargs):
        super().__init__(ifname, **kargs)

    def remove(self):
        """
        Remove interface from operating system. Removing the interface
        deconfigures all assigned IP addresses and clear possible DHCP(v6)
        client processes.

        Example:
        >>> from vyos.ifconfig import Interface
        >>> i = Interface('eth0')
        >>> i.remove()
        """
        # Do we have sub interfaces (VLANs)? We apply a regex matching
        # subinterfaces (indicated by a .) of a parent interface.
        #
        # As interfaces need to be deleted "in order" starting from Q-in-Q
        # we delete them first.
        vlan_ifs = [f for f in os.listdir(r'/sys/class/net')
                    if re.match(self.config['ifname'] + r'(?:\.\d+)(?:\.\d+)', f)]

        for vlan in vlan_ifs:
            Interface(vlan).remove()

        # After deleting all Q-in-Q interfaces delete other VLAN interfaces
        # which probably acted as parent to Q-in-Q or have been regular 802.1q
        # interface.
        vlan_ifs = [f for f in os.listdir(r'/sys/class/net')
                    if re.match(self.config['ifname'] + r'(?:\.\d+)', f)]

        for vlan in vlan_ifs:
            Interface(vlan).remove()

        # All subinterfaces are now removed, continue on the physical interface
        super().remove()

    def add_vlan(self, vlan_id, ethertype='', ingress_qos='', egress_qos=''):
        """
        A virtual LAN (VLAN) is any broadcast domain that is partitioned and
        isolated in a computer network at the data link layer (OSI layer 2).
        Use this function to create a new VLAN interface on a given physical
        interface.

        This function creates both 802.1q and 802.1ad (Q-in-Q) interfaces. Proto
        parameter is used to indicate VLAN type.

        A new object of type VLANIf is returned once the interface has been
        created.

        @param ethertype: If specified, create 802.1ad or 802.1q Q-in-Q VLAN
                          interface
        @param ingress_qos: Defines a mapping of VLAN header prio field to the
                            Linux internal packet priority on incoming frames.
        @param ingress_qos: Defines a mapping of Linux internal packet priority
                            to VLAN header prio field but for outgoing frames.

        Example:
        >>> from vyos.ifconfig import VLANIf
        >>> i = VLANIf('eth0')
        >>> i.add_vlan(10)
        """
        vlan_ifname = self.config['ifname'] + '.' + str(vlan_id)
        if not os.path.exists('/sys/class/net/{}'.format(vlan_ifname)):
            self._vlan_id = int(vlan_id)

            if ethertype:
                self._ethertype = ethertype
                ethertype = 'proto {}'.format(ethertype)

            # Optional ingress QOS mapping
            opt_i = ''
            if ingress_qos:
                opt_i = 'ingress-qos-map ' + ingress_qos
            # Optional egress QOS mapping
            opt_e = ''
            if egress_qos:
                opt_e = 'egress-qos-map ' + egress_qos

            # create interface in the system
            cmd = 'ip link add link {ifname} name {ifname}.{vlan} type vlan {proto} id {vlan} {opt_e} {opt_i}' \
                .format(ifname=self.config['ifname'], vlan=self._vlan_id, proto=ethertype, opt_e=opt_e, opt_i=opt_i)
            self._cmd(cmd)

        # return new object mapping to the newly created interface
        # we can now work on this object for e.g. IP address setting
        # or interface description and so on
        return VLANIf(vlan_ifname)

    def del_vlan(self, vlan_id):
        """
        Remove VLAN interface from operating system. Removing the interface
        deconfigures all assigned IP addresses and clear possible DHCP(v6)
        client processes.

        Example:
        >>> from vyos.ifconfig import VLANIf
        >>> i = VLANIf('eth0.10')
        >>> i.del_vlan()
        """
        vlan_ifname = self.config['ifname'] + '.' + str(vlan_id)
        VLANIf(vlan_ifname).remove()
