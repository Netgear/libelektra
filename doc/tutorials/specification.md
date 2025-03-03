# How to Write a Specification in Elektra

## Overview

### Introduction

In this tutorial you will learn how to interactively use the `SpecElektra` specification
language and `kdb` to write a configuration specification for an example application.

### What you should already know

- [how to install Elektra](https://www.libelektra.org/getstarted/guide#installation)
- basic Elektra commands and concepts (`kdb get`, `kdb set`, `kdb ls`)
- how to open and use a terminal

### What you’ll learn

- how to create and mount a specification using `kdb`
- how to add keys with different types, defaults and examples to your specification and how to validate them
- the benefits of using `kdb` to generate a specification, instead of writing one by hand
- how to use the final specification during the installation process of applications

### What you'll do

- use `kdb` to create and mount a specification for an example CRUD (Create, Read, Update, Delete) application
- define defaults, examples and checks for keys in the validation
- use the specification as a starting point for customizing the configuration of installed applications

## Example App Overview

For this tutorial you will write a specification for a simple CRUD backend application.
You need to configure a `port` and a `secure` property, that toggles SSL usage, for the REST server.
An `ip` and a SQL `dialect` for the database server the app
will connect to and finally a `date` where all the data will be saved to a backup.

So the application will need the following configuration options:

- a server port
- server secure
- a database ip
- a database dialect
- a backup date

## Getting Started

Make sure you have `Elektra` installed on your local machine:

```sh
kdb --version

# KDB_VERSION: 0.9.9
# SO_VERSION: 5
```

Otherwise refer to the [getting started guide](https://www.libelektra.org/getstarted/guide) to install it.

## Mounting the Specification

### Step 1: Mount a Specification File

First you need to mount a specification file, in this case `spec.ni` to the `spec:/` namespace.
You can define the path inside the `spec:/` namespace as `/tests/sw/org/app/#0/current`, refer to
[the documentation](https://www.libelektra.org/tutorials/integration-of-your-c-application) to find out more about constructing the name.

You will be using the profile `current`, you can find out more about profiles in
[the documentation](https://www.libelektra.org/plugins/profile) as well.

We will be writing values mostly to the `user:/` namespace. If you want to learn more about namespaces in general, refer to the
[the documentation on namespaces](https://www.libelektra.org/tutorials/namespaces)

You also need to specify the plugin you will use for writing to the file in the correct format. In this case you can choose the `ni` plugin to write to the specification file.

```sh
sudo kdb mount `pwd`/spec.ni spec:/tests/sw/org/app/\#0/current ni
```

> **_Attention_**: Mounting the specification by supplying an absolute path
> (like in the previous example with `` `pwd` ``) is only recommended for defining
> the specification in the first place.
> It is not recommended when mounting the final specification
> for usage with the application, especially not in production environments!
>
> Please read the section [Using the specification](#elektra-use-spec) at the end
> of this document for further information.

Using the command below you can get the location of the concrete file that is used by Elektra.

```sh
kdb file spec:/tests/sw/org/app/\#0/current
# /current/working/directory/spec.ni
```

### Step 2: Define a mountpoint

Next you can define, that this specification uses a specific mountpoint for a concrete application configuration.
So you can say the concrete configuration should be written to `app.ni`.

```sh
kdb meta-set spec:/tests/sw/org/app/\#0/current mountpoint app.ni
```

Your `spec.ni` file should now look something like this:

```sh
cat $(kdb file spec:/tests/sw/org/app/\#0/current)

# ;Ni1
# ; Generated by the ni plugin using Elektra (see libelektra.org).

# =

# []
#  meta:/mountpoint = app.ni
```

### Step 3: Do a specification mount

```sh
sudo kdb spec-mount /tests/sw/org/app/\#0/current ni
```

This specification mount makes sure that the paths where the concrete configuration should be (`app.ni`)
are ready to fulfill our specification (`spec.ni`).
Be aware that different files get mounted for different namespaces.
You've a specification file (`spec.ni`) for the `spec`-namespace and three files (`app.ni`) on different locations
for the `dir`- `user`- and `system`-namespaces.

You can see the files by providing the namespace as prefix to the `kdb file` command:

```sh
kdb file system:/tests/sw/org/app/#0/current
# /etc/kdb/app.ni

kdb file user:/tests/sw/org/app/#0/current
# /home/user/.config/app.ni

kdb file dir:/tests/sw/org/app/#0/current
# /current/working/directory/.dir/app.ni
```

> **_Note_**: The files only exist, when configuration values are stored there,
> i.e. they are created on the first `kdb set` and removed with the last `kdb rm`.

For more information about namespaces in Elektra please see [here](https://www.libelektra.org/manpages/elektra-namespaces),
a tutorial about the topic is available [here](https://www.libelektra.org/tutorials/namespaces).

## Adding your first key to the specification

### Step 1: Adding the server port

The first key you will add to your specification is the port of the server.
You add it by using the following command:

```sh
kdb meta-set spec:/tests/sw/org/app/\#0/current/server/port type unsigned_short
```

What you also specified in the command above is the type of the configuration value. Elektra uses the [CORBA type system](https://www.libelektra.org/plugins/type)
and will check if values conform to the type specified.

So after adding the initial key, your specification should look something like this:

```sh
cat $(kdb file spec:/tests/sw/org/app/\#0/current)


# ;Ni1
# ; Generated by the ni plugin using Elektra (see libelektra.org).

#  =
# server/port =

# []
#  meta:/mountpoint = app.ni

# [server/port]
#  meta:/type = unsigned_short
```

### Step 2: Adding more metadata

So with your first key added, you of course want to specify more information for the port. There surely is more information to a port than just the type.
What about a `default`, or what about an `example` for a usable port? Maybe a `description` what the port really is for?
Let's add that next!

```sh
kdb meta-set spec:/tests/sw/org/app/\#0/current/server/port default 8080
kdb meta-set spec:/tests/sw/org/app/\#0/current/server/port example 8080
kdb meta-set spec:/tests/sw/org/app/\#0/current/server/port description "port of the REST server that runs the application"
```

Beautiful! Your specification is starting to look like something useful.
But wait! Shouldn't a port just use values between `1` and `65535`?

Of course Elektra also has a plugin for that. You can just use the [network](https://www.libelektra.org/plugins/network) checker plugin.

```sh
kdb meta-set spec:/tests/sw/org/app/\#0/current/server/port check/port ''
```

Now we define the plugins that we want to load.
In our example we need the `ni`-Plugin for reading and writing the configuration files,
the `type`-plugin for validating data types and the `network`-plugin for validating port numbers.

```sh
kdb meta-set spec:/tests/sw/org/app/\#0/current infos/plugins "ni type network"
```

Nice!
You just have to do one more thing when using a new plugin. Elektra needs to remount the spec to use the new plugin.
Use the command from before:

```sh
sudo kdb spec-mount /tests/sw/org/app/\#0/current
```

Your final specification after adding the port should now look something like this:

```sh
cat $(kdb file spec:/tests/sw/org/app/\#0/current)

# ;Ni1
# ; Generated by the ni plugin using Elektra (see libelektra.org).

#  =
# server/port =

# []
#  meta:/mountpoint = app.ni
#  meta:/infos/plugins = ni type network

# [server/port]
#  meta:/check/port =
#  meta:/type = unsigned_short
#  meta:/example = 8080
#  meta:/description = port of the REST server that runs the application
#  meta:/default = 8080
```

You can now try to read the value of the newly created configuration.
Since you did not set the value to anything yet, you will get the default value back.

```sh
kdb get /tests/sw/org/app/\#0/current/server/port

#> 8080
```

Try to set the port to `65536` now.

```sh
kdb set user:/tests/sw/org/app/\#0/current/server/port 65536
# RET: 5
#  Sorry, 1 warning was issued ;(
#  1: Module network issued the warning C03200:
# 	Validation Semantic: Port 65536 on key user:/tests/sw/org/app/#0/current/server/port was not within 0 - 65535
# Sorry, module type issued the error C03200:
# Validation Semantic: The type 'unsigned_short' failed to match for 'user:/tests/sw/org/app/#0/current/server/port' with string '65536'
```

Did it work? I hope not. The validation plugins you specified will now correctly validate the port you enter and give you an error.

In this example, the `network` plugin and the `type` plugin are emitting warnings or errors,
because the valid ranges for `port` and `unsigned_short` are the same.

### Step 3: Adding boolean keys

Next up you will configure the `secure` property of our server. This boolean key will toggle if your server encrypts the communication via SSL.

So we will add the key and some metadata for it:

```sh
kdb meta-set spec:/tests/sw/org/app/\#0/current/server/secure type boolean
kdb meta-set spec:/tests/sw/org/app/\#0/current/server/secure default 1
kdb meta-set spec:/tests/sw/org/app/\#0/current/server/secure example 0
kdb meta-set spec:/tests/sw/org/app/\#0/current/server/secure description "true if the REST server uses SSL for communication"
```

By default the `type` plugin will normalize boolean values when setting them, before storing them.
This only works for the concrete config, so when setting the values for the spec you have to use the unnormalized values.
In the case it uses `1` for boolean `true` and `0` for boolean `false`.

Since the key `/sw/org/app/\#0/current/server/secure` has a default value of `1`,
we are able to retrieve the default value from the key database:

```sh
kdb get /tests/sw/org/app/\#0/current/server/secure

#> 1
```

You can read more about this in the documentation for the [type plugin](https://www.libelektra.org/plugins/type#normalization).

## Adding the database keys to the specification

### Step 1: Adding the database ip

Next up you will add a key for the database `ip` address. Like with the key before, you will add a `type`, `default`, `example` and a `description` so that the configuration will be easily usable.

Don't forget the most important rule of configurations: **Always add sensible defaults!**

Now let's try something different. What if you change the file manually? Will Elektra pick up on
the changes? And save you from writing **a lot** of `kdb` commands?

_of course_

So just open your file using good old `vim` and add the following lines to specify configuration for the `ip` address.

```
vim $(kdb file spec:/tests/sw/org/app/\#0/current)

# ;Ni1
# ; Generated by the ni plugin using Elektra (see libelektra.org).

database/ip =
#  =
# server/port =
# server/secure =

[database/ip]
 meta:/check/ipaddr =
 meta:/type = string
 meta:/example = 127.0.0.1
 meta:/description = ip address of the database server, that the application will connect to
 meta:/default = 127.0.0.1

# []
#  meta:/mountpoint = app.ni
#  meta:/infos/plugins = ni type network

# [server/port]
#  meta:/check/port =
#  meta:/type = unsigned_short
#  meta:/example = 8080
#  meta:/description = port of the REST server that runs the application
#  meta:/default = 8080

# [server/secure]
#  meta:/type = boolean
#  meta:/example = 0
#  meta:/description = true if the REST server uses SSL for communication
#  meta:/default = 1
```

Alternatively you can of course use `kdb` again to set the configuration values that way. Here are the commands to do that.

```sh
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/ip type string
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/ip default 127.0.0.1
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/ip example 127.0.0.1
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/ip description "ip address of the database server, that the application will connect to"
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/ip check/ipaddr ''
```

### Step 2: Adding the database dialect

Next up you will add a key for the SQL `dialect` the database will use. Since there are only a few databases your application will support,
you can define the possible dialects via an [enum](https://www.libelektra.org/plugins/type#enums) type.
This allows us to prohibit all other possible dialects that are not SQL.

First you define the size of the `enum` type, and then you can add the different `enum` values.

```sh
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/dialect type enum
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/dialect check/enum "#4"
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/dialect check/enum/\#0 postgresql
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/dialect check/enum/\#1 mysql
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/dialect check/enum/\#2 mssql
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/dialect check/enum/\#3 mariadb
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/dialect check/enum/\#4 sqlite
```

Afterwards you define all the other parameters, just as before.

```sh
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/dialect default sqlite
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/dialect example mysql
kdb meta-set spec:/tests/sw/org/app/\#0/current/database/dialect description "SQL dialect of the database server, that the application will connect to"
```

After this meta-setting bonanza your specification file should look something like this:

```sh
cat $(kdb file spec:/tests/sw/org/app/\#0/current)

# ;Ni1
# ; Generated by the ni plugin using Elektra (see libelektra.org).

# database/ip =
#  =
# server/port =
# server/secure =
# database/dialect =

# [database/ip]
#  meta:/check/ipaddr =
#  meta:/type = string
#  meta:/example = 127.0.0.1
#  meta:/description = ip address of the database server, that the application will connect to
#  meta:/default = 127.0.0.1

# []
#  meta:/mountpoint = app.ni
#  meta:/infos/plugins = ni type network

# [server/port]
#  meta:/check/port =
#  meta:/type = unsigned_short
#  meta:/example = 8080
#  meta:/description = port of the REST server that runs the application
#  meta:/default = 8080

# [server/secure]
#  meta:/type = boolean
#  meta:/example = 0
#  meta:/description = true if the REST server uses SSL for communication
#  meta:/default = 1

# [database/dialect]
#  meta:/check/enum/#2 = mssql
#  meta:/check/enum/\#0 = postgresql
#  meta:/type = enum
#  meta:/check/enum/#1 = mysql
#  meta:/example = mysql
#  meta:/description = SQL dialect of the database server, that the application will connect to
#  meta:/check/enum/#4 = sqlite
#  meta:/check/enum/#3 = mariadb
#  meta:/default = sqlite
#  meta:/check/enum = #4
```

## Adding the backup date

The last key you will add to our specification is a `date` key for the annual backup and restart (this should probably not be annually in a real application).
Here you use the [check/date](https://www.libelektra.org/plugins/date) plugin with the `ISO8601` format.
You also specify a `check/date/format`. You can find all possible date formats on the [plugin page](https://www.libelektra.org/plugins/date).
For this you can use the following commands:

```
kdb meta-set spec:/tests/sw/org/app/\#0/current/backup/date type string
kdb meta-set spec:/tests/sw/org/app/\#0/current/backup/date check/date ISO8601
kdb meta-set spec:/tests/sw/org/app/\#0/current/backup/date check/date/format "calendardate complete extended"
```

Then just add examples, defaults and description as always.

```
kdb meta-set spec:/tests/sw/org/app/\#0/current/backup/date default 2021-11-01
kdb meta-set spec:/tests/sw/org/app/\#0/current/backup/date example 2021-01-12
kdb meta-set spec:/tests/sw/org/app/\#0/current/backup/date description "date of the annual server and database backup"
```

Now we add the validation plugin for dates and remount the specification:

```
kdb meta-set spec:/tests/sw/org/app/\#0/current infos/plugins "ni type network date"
sudo kdb spec-mount /tests/sw/org/app/\#0/current
```

If we try to add a value that is not in the specified format, an error should get emitted.

```
kdb set user:/tests/sw/org/app/\#0/current/backup/date "03.04.2022"
# RET: 5
# Sorry, module date issued the error C03100:
# Validation Syntactic: Date '03.04.2022' doesn't match iso specification calendardate complete extended
```

To double-check if things are correct, we try to get the value from the `user`-namespace
and via cascading lookup.

```
kdb get user:/tests/sw/org/app/\#0/current/backup/date
# RET: 11
# STDERR: Did not find key 'user:/tests/sw/org/app/#0/current/backup/date'

kdb get /tests/sw/org/app/\#0/current/backup/date
#> 2021-11-01
```

As expected, no value was written to the `user`-namespace and a cascading lookup returns
the date that was given as default value in the specification.
If we now use the correct format, the new date should be stored in the `user`-namespace and retrieved
with both `kdb get` lookups.

```
kdb set user:/tests/sw/org/app/\#0/current/backup/date "2022-04-03"
#> Create a new key user:/tests/sw/org/app/#0/current/backup/date with string "2022-04-03"

kdb get user:/tests/sw/org/app/\#0/current/backup/date
#> 2022-04-03

kdb get /tests/sw/org/app/\#0/current/backup/date
#> 2022-04-03
```

If we explicitly query the `system`-namespace, no key is found.

```
kdb get system:/tests/sw/org/app/\#0/current/backup/date
# RET: 11
# STDERR: Did not find key 'system:/tests/sw/org/app/#0/current/backup/date'
```

## Final specification code

Your specification should be complete now!
After adding all the keys that are necessary for our application, your specification should look something like this:

```
cat $(kdb file spec:/tests/sw/org/app/\#0/current)

# ;Ni1
# ; Generated by the ni plugin using Elektra (see libelektra.org).

# backup/date =
# database/ip =
#  =
# server/port =
# server/secure =
# database/dialect =

# [backup/date]
#  meta:/check/date/format = calendardate complete extended
#  meta:/type = string
#  meta:/example = 2021-01-12
#  meta:/description = date of the annual server and database backup
#  meta:/default = 2021-11-01
#  meta:/check/date = ISO8601

# [database/ip]
#  meta:/check/ipaddr =
#  meta:/type = string
#  meta:/example = 127.0.0.1
#  meta:/description = ip address of the database server, that the application will connect to
#  meta:/default = 127.0.0.1

# []
#  meta:/mountpoint = app.ni
#  meta:/infos/plugins = ni type network date

# [server/port]
#  meta:/check/port =
#  meta:/type = unsigned_short
#  meta:/example = 8080
#  meta:/description = port of the REST server that runs the application
#  meta:/default = 8080

# [server/secure]
#  meta:/type = boolean
#  meta:/example = 0
#  meta:/description = true if the REST server uses SSL for communication
#  meta:/default = 1

# [database/dialect]
#  meta:/check/enum/#2 = mssql
#  meta:/check/enum/\#0 = postgresql
#  meta:/type = enum
#  meta:/check/enum/#1 = mysql
#  meta:/example = mysql
#  meta:/description = SQL dialect of the database server, that the application will connect to
#  meta:/check/enum/#4 = sqlite
#  meta:/check/enum/#3 = mariadb
#  meta:/default = sqlite
#  meta:/check/enum = #4
```

<a id="elektra-use-spec"></a>

## Using the specification

Now, after you've finished your specification and want to use it for daily business, some aspects have to be considered.
A specification usually is written to cover the most common use cases and to provide sensible defaults.
In some cases, the administrator may want to change the specification, e.g. for extending it
or introducing further restrictions.

In such cases, **directly changing** the specification that was designed for
and delivered with the application, is **not** the **recommended** approach.

The recommended way is making a **copy** of the default specification
while installing the application and then saving changes to that copy.
If misconfiguration occurs, you can easily look at the default specification or reapply it to start over.

If you mount the specification with an absolute path (e.g. by using `` `pwd` `` in scripts),
like it was done for defining the specification with `kdb`, the file gets changed directly.
If `` `pwd` `` refers to the installation directory of the application, this would be totally fine,
but if this is done during development and `` `pwd` `` refers to the source directory, the source specification would be
modified via `kdb set spec:/...` calls.

First we have to unmount our original configuration file we just created:

```sh
sudo kdb umount spec:/tests/sw/org/app/\#0/current
```

The **recommended way** to apply the specification is:

```
# choose a unique filename for your application instead of spec.ni
sudo kdb mount spec.ni spec:/tests/sw/org/app/\#0/current ni
sudo kdb import spec:/tests/sw/org/app/\#0/current ni ./spec.ni
```

Because we used a relative path (not starting with `/`), Elektra will use a file
within the `spec` directory (`/usr/share/elektra/specification` by default) for storing the specification.

The `kdb import` command just tells Elektra to load the file `./spec.ni`
with the `ni` plugin and write it into `spec:/tests/sw/org/app/\#0/current`.
Using a separate `kdb import` also means we could use a different storage plugin
for mounting than what `./spec.ni` uses.

Another alternative is copying the file manually:

```
sudo kdb mount spec.ni spec:/tests/sw/org/app/\#0/current ni
sudo cp ./spec.ni $(kdb file spec:/tests/sw/org/app/\#0/current)
```

This works like the previous snippet, except that we directly modify the spec file without going through Elektra.
For very big specifications this might be faster, but we get no validation that the file is actually readable
and `./spec.ni` has to be readable by the storage plugin used with `kdb mount`.

Finally, in some cases you may want to control where the mounted spec file is stored
(e.g. if you are updating a legacy application that has an existing configuration directory).
In those cases using an absolute path is fine:

```
kdb mount /etc/spec.ni spec:/tests/sw/org/app/\#0/current ni
kdb import spec:/tests/sw/org/app/\#0/current ni ./my-spec.ini
```

or

```
sudo kdb mount /etc/spec.ni spec:/tests/sw/org/app/\#0/current ni
sudo cp ./spec.ni $(kdb file spec:/tests/sw/org/app/\#0/current)
```

Please note that also in these examples, the file referred to
by the absolute path `/etc/spec.ni` is a **new file**
where the content of the file `./spec.ni` in the working directory gets imported or copied to.

## Cleanup

If you want to remove the files that were created in the course of the tutorial, the following steps are necessary.

```
sudo rm -v `kdb file spec:/tests/sw/org/app/#0/current`
rm -v `kdb file user:/tests/sw/org/app/#0/current`
sudo rm -v /usr/share/elektra/specification/spec.ni
sudo rm -v /etc/spec.ni
```

If you take a look at `kdb mount`, you'll see that there are currently two mountpoints open.

Mountpoints are meant to mount (external) files into the key database structure of Elektra.
This mechanism is similar to `mount` on Linux:
changes made to the key database will be written to the underlying mounted file.
If you want to learn more on mounting and mountpoints in Eletra, refer to [the documentation](https://www.libelektra.org/tutorials/mount-configuration-files).

To round up this tutorial, we will `kdb umount` these two mountpoints:

```sh
rm -v ./spec.ni
sudo kdb umount /tests/sw/org/app/#0/current
```

```
sudo kdb umount spec:/tests/sw/org/app/#0/current
```

In case something went wrong and you want to reset the whole content of your kdb,
please refer to [the manpage of kdb reset](https://www.libelektra.org/manpages/kdb-reset).

## Summary

- You set up and mounted a specification using `kdb mount` and `kdb spec-mount`.
- You added keys to the specification using `kdb meta-set`.
- You added different types of keys with `type string`, `type boolean` or `type unsigned_short`.
- You added keys with `enum types`, to restrict specific configuration settings to a defined set of possible values.
- You added default parameters, examples and descriptions with `example`, `default`, `description`.
- You also added validation checks using different plugins, like `check/port` or `check/date`.
- You know how to use the specification for installed applications (esp. in production environments).

## Learn more

- [Tutorial Overview](https://www.libelektra.org/tutorials/readme)
