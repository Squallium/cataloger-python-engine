#!/usr/bin/env node

import dotenv = require('dotenv');

/**
 * initialize environmental configuration
 */
dotenv.config({ path: 'configs/' + process.env.ENV + '.env'})
dotenv.config({ path: 'configs/secret/' + process.env.ENV + '.env'})

console.log(process.env.PORT)

/**
 * Initialize backend microservice
 */
import {StartUp} from "@cataloger/core/bin/www";
import {{ "{" }}{{cookiecutter.project_camel_case}}MicroServiceApp{{ "}" }} from "../app";

const startUp: StartUp = new StartUp(new {{cookiecutter.project_camel_case}}MicroServiceApp());
startUp.startUpSequence();
