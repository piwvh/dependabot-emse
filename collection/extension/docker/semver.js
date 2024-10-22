const semver = require('semver')

let cmd_args = process.argv.slice(2);
if(cmd_args.length < 2) {
    console.error('Invalid args')
    process.exit(1);
}

let func = cmd_args.shift();

let output = null;
if (['sort', 'rsort'].indexOf(func) !== -1) {
    output = semver[func](cmd_args);
}
else if (['minSatisfying', 'maxSatisfying'].indexOf(func) !== -1) {
    let pattern = cmd_args.pop()
    output = semver[func](cmd_args, pattern);
}
else {
    output = semver[func](...cmd_args);
}

console.log(JSON.stringify({
    'function': func,
    'args': cmd_args,
    'output': output
}))