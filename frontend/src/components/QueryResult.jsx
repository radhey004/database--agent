import {
  CheckCircle2,
  Database,
  Table2,
} from "lucide-react";


function QueryResult({
  result,
}) {

  if (!result) {

    return null;

  }


  /*
    Normalize possible result formats.

    Read query:
    {
      success: true,
      query: "...",
      row_count: 10,
      rows: [...]
    }

    Modification:
    {
      success: true,
      operation: "CREATE",
      target: "test_table",
      affected_rows: -1
    }
  */

  const data =
    typeof result === "object"
      ? result
      : {};


  const rows =
    Array.isArray(
      data.rows
    )
      ? data.rows
      : Array.isArray(
          result
        )
        ? result
        : [];


  const columns =
    rows.length > 0
      ? Object.keys(
          rows[0]
        )
      : [];


  const isModification =
    data.operation ||
    data.affected_rows !==
      undefined;


  const rowCount =
    data.row_count ??
    data.affected_rows ??
    rows.length;


  const formatValue = (
    value
  ) => {

    if (value === null) {

      return "NULL";

    }


    if (
      typeof value ===
      "object"
    ) {

      return JSON.stringify(
        value
      );

    }


    return String(
      value
    );

  };


  /*
    Modification result
  */

  if (isModification) {

    return (

      <div className="modification-result">

        <div className="result-success-header">

          <div className="result-success-icon">

            <CheckCircle2
              size={20}
            />

          </div>


          <div>

            <h4>
              Modification Executed
            </h4>

            <p>
              Database changes were completed successfully.
            </p>

          </div>

        </div>


        <div className="result-meta-grid">

          {data.operation && (

            <div className="result-meta-item">

              <span>
                Operation
              </span>

              <strong>
                {data.operation}
              </strong>

            </div>

          )}


          {data.target && (

            <div className="result-meta-item">

              <span>
                Target
              </span>

              <strong>
                {data.target}
              </strong>

            </div>

          )}


          <div className="result-meta-item">

            <span>
              Status
            </span>

            <strong className="success-text">
              Success
            </strong>

          </div>


          {rowCount !== -1 &&
            rowCount !== null &&
            rowCount !== undefined && (

              <div className="result-meta-item">

                <span>
                  Affected Rows
                </span>

                <strong>
                  {rowCount}
                </strong>

              </div>

            )}

        </div>

      </div>

    );

  }


  /*
    Empty result
  */

  if (
    rows.length === 0
  ) {

    return (

      <div className="query-result empty-result">

        <Database
          size={20}
        />

        <div>

          <strong>
            Query completed successfully
          </strong>

          <p>
            No rows were returned.
          </p>

        </div>

      </div>

    );

  }


  /*
    SELECT result
  */

  return (

    <div className="query-result">

      <div className="query-result-header">

        <div className="query-result-title">

          <Table2
            size={18}
          />

          <span>
            Query Result
          </span>

        </div>


        <div className="row-count-badge">

          {rowCount}
          {" "}
          {rowCount === 1
            ? "row"
            : "rows"}

        </div>

      </div>


      <div className="result-table-wrapper">

        <table className="result-table">

          <thead>

            <tr>

              {columns.map(
                (column) => (

                  <th
                    key={column}
                  >
                    {column}
                  </th>

                )
              )}

            </tr>

          </thead>


          <tbody>

            {rows.map(
              (
                row,
                index
              ) => (

                <tr
                  key={index}
                >

                  {columns.map(
                    (
                      column
                    ) => (

                      <td
                        key={column}
                      >
                        {formatValue(
                          row[column]
                        )}
                      </td>

                    )
                  )}

                </tr>

              )
            )}

          </tbody>

        </table>

      </div>

    </div>

  );

}


export default QueryResult;