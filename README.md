# Vmware
Script that by connecting to a one or more vCenters or ESXi collects the current snapshots present with details based on the age of the snapshot introduced as a parameter.

Output is a pretty table with the name, description, host, datastore and age details of each snapshot.
+-------------+----------------------+----------------+--------------------------------------------------+----------------------+--------------+
|   Vm Name   |         Host         |   Datastore    |                  Snapshot Name                   | Snapshot Description | Snapshot Age |
+-------------+----------------------+----------------+--------------------------------------------------+----------------------+--------------+
|  mywebsrv1  | myesxi01.example.com | mydatastore001 |            Initial setup and  config             |       whatever       |     145      |
|  mydataba1  | myesxi02.example.com | mydatastore002 |          Basic config except user cert           |      you prefer      |     101      |
+-------------+----------------------+----------------+--------------------------------------------------+----------------------+--------------+

The same is also saved to a CSV on the current directory.
