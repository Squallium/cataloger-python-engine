import {ConnectOptions, createConnection, Model} from "mongoose";

// Lazy Begin Imports
// Lazy End Imports

const uri: string = process.env.MONGO_URI_{{ cookiecutter.project_screaming_snake }} || "";
const options: ConnectOptions = {};
export const {{cookiecutter.project_camel_case}}Conn = createConnection(uri, options);

// Lazy Begin
// Lazy End
